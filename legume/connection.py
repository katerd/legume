# -*- coding: utf-8 -*-
# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

__docformat__ = 'restructuredtext'

import struct
import random
import logging
import netshared
import timing as time
from nevent import Event
from pingsampler import PingSampler
from bitfield import bitfield
from bytebuffer import ByteBuffer
import messages
import errno

PING_REQUEST_FREQUENCY = 2.0
CONNECTION_LOSS = 0

class OutgoingMessage(object):
    def __init__(self, message_id, message_bytes, require_ack):
        self.message_id = message_id
        self.message_bytes = message_bytes
        self.require_ack = require_ack

        '''
        If this message requires an ack this timestamp will
        either be None (not yet sent), or a value obtained
        from time.time() indicating when the message was last sent.
        The EndpointBuffer will not send a packet until 2xRTT ms
        has elapsed between send attempts.
        '''
        self.last_send_attempt_timestamp = None

    @property
    def length(self):
        return len(self.message_bytes)

class Connection(object):

    MTU = 1400
    MESSAGE_TRANSPORT_HEADER = 'HHB'
    RECENT_MESSAGE_LIST_SIZE = 1000
    MINIMUM_RESEND_DELAY_MS = 10 / 1000.0

    _log = logging.getLogger('legume.Connection')

    def __init__(self, parent=None, message_factory=None):
        if message_factory is None:
            self.message_factory = parent.message_factory
        else:
            self.message_factory = message_factory

        self.parent = parent
        self._last_receive_timestamp = time.time()
        self._last_send_timestamp = time.time()
        self._keep_alive_send_timestamp = time.time()
        self._keep_alive_message_id = 0

        # server: number of keepalives sent
        # client: number of keepalives received
        self._keepalive_count = 0

        self._ping_id = 0
        self._ping_send_timestamp = time.time()
        self._ping_meter = PingSampler()

        self.OnConnectRequestAccepted = Event()
        self.OnConnectRequestRejected = Event()
        self.OnConnectRequest = Event()
        self.OnError = Event()
        self.OnMessage = Event()
        self.OnDisconnect = Event()

        # Packet instances to be processed go in here
        self._incoming_messages = []

        # List of OutgoingMessages
        self._outgoing = []

        # In-order packet instances that have arrived early
        self._incoming_out_of_sequence_messages = []

        self._incoming_ordered_sequence_number = 0
        self._outgoing_ordered_sequence_number = 1
        self._outgoing_message_id = 0
        self._recent_message_ids = []

        # Metrics
        self._in_bytes = 0
        self._out_bytes = 0
        self._in_packets = 0
        self._out_packets = 0
        self._in_messages = 0
        self._out_messages = 0

        '''
        Default transport latency is high - This prevents spamming
        of the network prior to obtaining a calculated latency.
        '''
        self._transport_latency = 0.3 # 0.1 = 100ms

    @property
    def out_buffer_bytes(self):
        return sum([len(o.message_bytes) for o in self._outgoing])

    @property
    def latency(self):
        return self._ping_meter.get_ping()

    @property
    def in_bytes(self):
        return self._in_bytes

    @property
    def out_bytes(self):
        return self._out_bytes

    @property
    def reorder_queue(self):
        return len(self._incoming_out_of_sequence_messages)

    @property
    def keepalive_count(self):
        return self._keepalive_count

    # ------------- Public Methods -------------

    def process_inbound_packet(self, data):
        self._in_packets += 1
        self._process_inbound_packet(data)

    def update(self):
        '''
        Send any packets that are in the output buffer and read
        any packets that have been received.
        '''
        try:
            self.parent.do_read(self._on_socket_data)
        except netshared.NetworkEndpointError, e:
            self.raiseOnError('Connection reset by peer')
            return

        if self._ping_meter.has_estimate():
            self._transport_latency = self._ping_meter.get_ping()

        read_messages = self._update(
                        self.parent._socket, self.parent._address)

        if len(read_messages) != 0:
            self._last_receive_timestamp = time.time()

        for message in read_messages:

            if self.message_factory.is_a(message, 'ConnectRequestAccepted'):
                self.OnConnectRequestAccepted(self, None)

            elif self.message_factory.is_a(message, 'ConnectRequestRejected'):
                self.OnConnectRequestRejected(self, None)

            elif self.message_factory.is_a(message, 'KeepAliveResponse'):

                if (message.id.value == self._keep_alive_message_id):
                    self._ping_meter.add_sample(
                        (time.time()-self._keep_alive_send_timestamp)*1000)
                else:
                    self._log.warning('Received old keep-alive, discarding')

            elif self.message_factory.is_a(message, 'KeepAliveRequest'):
                self._keepalive_count += 1
                response = self.message_factory.get_by_name('KeepAliveResponse')()
                response.id.value = message.id.value
                self.send_message(response)

            elif self.message_factory.is_a(message, 'Pong'):
                if (message.id.value == self._ping_id):
                    self._ping_meter.add_sample(
                      (time.time()-self._ping_send_timestamp)*1000)
                else:
                    self._log.warning('Received old Pong, discarding')

            elif self.message_factory.is_a(message, 'Ping'):
                self._send_pong(message.id.value)

            elif self.message_factory.is_a(message, 'Disconnected'):
                self._log.debug('Received `Disconnected` message')
                self.OnDisconnect(self, None)

            elif self.message_factory.is_a(message, 'MessageAck'):
                self._process_message_ack(message.message_to_ack.value)

            elif self.message_factory.is_a(message, 'ConnectRequest'):
                # Unless the connection request is explicitly denied then
                # a connection is made - OnConnectRequest may return None
                # if no event handlers are bound.
                accept = True

                if (message.protocol.value != netshared.PROTOCOL_VERSION):
                    self._log.error('Invalid protocol version for client')
                    accept = False
                if self.OnConnectRequest(self.parent, message) is False:
                    accept = False

                if accept:
                    response = self.message_factory.get_by_name('ConnectRequestAccepted')
                    self.send_reliable_message(response())
                else:
                    response = self.message_factory.get_by_name('ConnectRequestRejected')
                    self.send_reliable_message(response())
                    self.pendingDisconnect = True
            else:
                self.OnMessage(self, message)


        if (time.time() > self._ping_send_timestamp + PING_REQUEST_FREQUENCY):
            if self.parent.is_server:
                self._keep_alive_send_timestamp = time.time()
            self._send_ping()


        if self.parent.is_server:
            # Server sends keep alive requests...
            if ((time.time()-self._keep_alive_send_timestamp)>
               (self.parent.timeout/2)):
                self._send_keep_alive()
            # though it will eventually give up...
            if (time.time()-self._last_receive_timestamp)>(self.parent.timeout):
                self.OnError(self, 'Connection timed out')
        else:
            # ...Client waits for the connection to timeout
            if (time.time()-self._last_receive_timestamp)>(self.parent.timeout):
                self._log.info('Connection has timed out')
                self.OnError(self, 'Connection timed out')

    def send_message(self, message, ordered=False, reliable=False):
        '''
        Send a message and specify any options for the send method used.
        A message sent inOrder is implicitly sent as reliable.
        message is an instance of a subclass of packets.BasePacket.
        Returns the number of bytes added to the output queue for this
        message (header + message).
        '''
        self._last_send_timestamp = time.time()

        self._outgoing_message_id += 1
        message_id = self._outgoing_message_id
        if ordered:
            self._outgoing_ordered_sequence_number += 1
            inorder_sequence_number = self._outgoing_ordered_sequence_number
        else:
            inorder_sequence_number = 0

        packet_flags = bitfield()
        packet_flags[0] = int(ordered)
        packet_flags[1] = int(reliable)

        message_transport_header = struct.pack(
            '!'+self.MESSAGE_TRANSPORT_HEADER,
            message_id, inorder_sequence_number, int(packet_flags))

        message_bytes = message.get_packet_bytes()
        total_length = len(message_bytes)+len(message_transport_header)
        self._out_bytes += total_length

        self._add_message_bytes_to_output_list(
            message_id,
            message_transport_header+message_bytes,
            ordered or reliable)

        self._log.debug('Packet data length = %s' % len(message_bytes))
        self._log.debug('Header length = %s' % len(message_transport_header))
        self._log.debug('Added %d byte %s packet in outgoing buffer' %
            (total_length, message.__class__.__name__))

        return total_length

    def send_reliable_message(self, message):
        '''
        Send a message that is guaranteed to be delivered.
        message is an instance of a subclass of packets.BasePacket
        '''
        self.send_message(message, False, True)

    def send_inorder_message(self, message):
        '''
        Send a message in the in-order channel. Any packets sent in-order will
        arrive in the order they were sent.
        message is an instance of a subclass of packets.BasePacket
        '''
        self.send_message(message, True)

    def has_outgoing_packets(self):
        '''
        Returns whether this buffer has any packets waiting to be sent.
        '''
        return len(self._outgoing) > 0

    # ------------- Private Methods -------------

    def _on_socket_data(self, data, addr):
        self._process_inbound_packet(data)

    def _send_keep_alive(self):
        self._keep_alive_message_id += 1
        if (self._keep_alive_message_id > netshared.USHRT_MAX):
            self._keep_alive_message_id = 0

        message = self.message_factory.get_by_name('KeepAliveRequest')()
        message.id.value = self._keep_alive_message_id

        self.send_message(message)
        self._keep_alive_send_timestamp = time.time()
        self._keepalive_count += 1

    def _send_ping(self):
        self._ping_id += 1
        if (self._ping_id > netshared.USHRT_MAX):
            self._ping_id = 0

        ping = self.message_factory.get_by_name('Ping')()
        ping.id.value = self._ping_id
        self.send_message(ping)
        self._ping_send_timestamp = time.time()

    def _send_pong(self, pingID):
        pong = self.message_factory.get_by_name('Pong')()
        pong.id.value = pingID
        self.send_message(pong)

    def _process_message_ack(self, message_id):
        for m in self._outgoing:
            if m.message_id == message_id:
                self._outgoing.remove(m)
                return

        self._log.warning('Got duplicate ACK for packet. message_id=%s' % (
            message_id))


    def _parse_packet(self, packet_bytes):
        '''
        Parse a raw udp packet and return a list of parsed messages.
        '''

        byte_buffer = ByteBuffer(packet_bytes)
        parsed_messages = []

        while not byte_buffer.is_empty():

            message_id, sequence_number, message_flags = \
                byte_buffer.read_struct(self.MESSAGE_TRANSPORT_HEADER)

            message_type_id = messages.BaseMessage.read_header_from_byte_buffer(
                byte_buffer)[0]
            message = self.message_factory.get_by_id(message_type_id)()
            message.read_from_byte_buffer(byte_buffer)

            # - These flags are for consumption by .update()
            message_flags_bf = bitfield(message_flags)
            message.is_reliable = message_flags_bf[1]
            message.is_ordered = message_flags_bf[0]

            message.sequence_number = sequence_number
            message.message_id = message_id

            parsed_messages.append(message)

        return parsed_messages

    def _process_inbound_packet(self, packet_bytes):
        '''
        Pass raw udp packet data to this method.
        Returns the number of packets parsed and inserted into
        the .incoming list.
        '''
        self._log.debug('%d bytes of packet_bytes read' % len(packet_bytes))
        messages_to_read = self._parse_packet(packet_bytes)

        self._in_bytes += len(packet_bytes)

        self._log.debug('parsed %d messages from packet' % len(messages_to_read))

        for message in messages_to_read:
            if not message.message_id in self._recent_message_ids:
                self._log.debug('Message ordered flag %s' % str(message.is_ordered))
                if message.is_ordered:
                    if self._can_read_inorder_message(seqNum):
                        self._insert_message(message)
                    else:
                        self._incoming_out_of_sequence_messages.append(message)
                        self._recent_message_ids.append(message.message_id)

                else:
                    self._insert_message(message)

        return len(messages_to_read)

    def _update(self, sock, address):
        '''
        Update this buffer by sending any messages in the output lists
        and read any messages which have been insert into the inputBuffer
        via the process_inbound_packet call.

        Returns a list of message instances of messages that were read.
        '''
        read_packets = self._do_read()
        self._truncate_recent_message_list()
        self._do_write(sock, address)

        return read_packets

    def _add_message_bytes_to_output_list(self, message_id,
                                     message_bytes, require_ack=False):
        if len(message_bytes) > self.MTU:
            raise BufferError, 'Packet is too large. size=%s, mtu=%s' % (
                len(message_bytes), self.MTU)
        else:
            self._outgoing.append(
                OutgoingMessage(message_id, message_bytes, require_ack))

    def _can_read_inorder_message(self, sequence_number):
        '''
        Can the in-order message with the specified sequence number be
        insert into the .incoming list for processing?
        '''
        return self._incoming_ordered_sequence_number == (sequence_number+1)

    def _create_packet(self):
        packet_size = 0
        packet_bytes = ""

        sent_messages = []

        self._log.debug('%d packets pending' % len(self._outgoing))

        for message in self._outgoing:

            if message.require_ack:

                # a minimum resend delay is required for two reasons:
                # 1. deadlock with a 0ms latency connection causes _do_write
                #    to never exit as _create_packet always returns data.
                # 2. resending every 0ms is just plain stupid.

                t = time.time()
                resend_delay = max(self.MINIMUM_RESEND_DELAY_MS, self._transport_latency)

                self._log.debug('LSAT: %s' % str(message.last_send_attempt_timestamp))
                self._log.debug('l8nc: %s' % str(self._transport_latency))
                self._log.debug('time: %s' % t)
                self._log.debug('rsnd: %s' % resend_delay)

                if message.last_send_attempt_timestamp is not None:
                    if ((message.last_send_attempt_timestamp +
                      resend_delay) >= t):
                        self._log.debug('Waiting for ack.')
                        continue

            if packet_size + message.length <= self.MTU:
                self._log.debug('Added data message into UDP packet')
                packet_size += message.length
                packet_bytes += message.message_bytes
                message.last_send_attempt_timestamp = time.time()
                sent_messages.append(message)
            else:
                self._log.debug('packet at MTU limit.')

        for sent_message in sent_messages:
            # Packets that require an ack are only removed
            # from the outgoing list if an ack is received.
            if not sent_message.require_ack:
                self._log.info('Message %d doesnt require ack - removing' %
                    sent_message.message_id)
                self._outgoing.remove(sent_message)
            else:
                self._log.info(
                    'Message %d requires ack - waiting for response' %
                    sent_message.message_id)

        return packet_bytes

    def _do_read(self):
        unheld_messages = []
        for held_message in self._incoming_out_of_sequence_messages:

            if self._can_read_inorder_message(held_message.sequence_number):
                unheld_messages.append(held_message)

                self._incoming_inorder_sequence_number = message.sequence_number
                self._incoming_messages.append(held_message)

        for unheld_message in unheld_messages:
            self._incoming_out_of_sequence_messages.remove(unheld_message)

        for message in self._incoming_messages:
            self._log.debug('Incoming message:')
            self._log.debug('IsInOrder: %d' % message.is_ordered)
            self._log.debug('IsReliable:%d' % message.is_reliable)
            self._log.debug('MessageID :%d' % message.message_id)
            if message.is_ordered or message.is_reliable:
                ack_message = messages.MessageAck()
                ack_message.message_to_ack.value = message.message_id
                self.send_message(ack_message)
                self._log.info(
                  'Informing of reciept of message %d' % message.message_id)

        read_messages = self._incoming_messages
        self._incoming_messages = []

        return read_messages

    def _do_write(self, sock, address):
        # TODO: combine _create_packet into this method, eg:
        #   while has_messages:
        #     add_message_to_packet
        #     is packet_full?
        #       send_packet
        #   is packet_partially_full?
        #     send_packet

        while True:
            packet = self._create_packet()
            if not packet:
                break

            if ((CONNECTION_LOSS == 0) or (random.randint(1, 100) > CONNECTION_LOSS)):
                try:
                    bytes_sent = sock.sendto(packet, 0, address)
                    self._out_packets += 1
                except IOError, e:
                    # HACK: ewouldblocks are ignored and the packet is silently
                    # discarded. Packet sending should be re-written to
                    # only remove messages from the send queue if the socket
                    # operation completes successfully.
                    errornum = e[0]
                    if errornum != errno.EWOULDBLOCK:
                        raise
            else:
                self._log.info('Simulated packet loss')

            self._log.info('Sent UDP packet %d bytes in length' % len(packet))

    def _insert_message(self, message):
        self._incoming_messages.append(message)
        self._recent_message_ids.append(message.message_id)
        if message.is_ordered:
            self._incoming_ordered_sequence_number = message.sequence_number

    def _truncate_recent_message_list(self):
        '''
        Ensures that the recentMessageIDs list length is kept below
        MAX_RECENT_PACKET_LIST_SIZE. This method is called as part of this class'
        update method.
        '''
        if len(self._recent_message_ids) > self.RECENT_MESSAGE_LIST_SIZE:
            self._recent_message_ids = \
                self._recent_message_ids[-self.RECENT_MESSAGE_LIST_SIZE:]
