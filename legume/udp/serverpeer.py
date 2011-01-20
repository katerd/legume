# legume. Copyright 2009 Dale Reidy. All rights reserved.
# See LICENSE for details.

__docformat__ = 'restructuredtext'

import logging
import legume.timing as time
import netshared
import connection
from legume.nevent import Event

LOG = logging.getLogger('legume.peer')

class Peer(object):
    '''
    A connection to the server. Each connected Client has a paired
    Peer object instance on the server.
    '''
    def __init__(self, parent, address):
        self._connected = False
        self.parent = parent
        self._socket = parent.socket
        self._address = address
        self._last_receive_timestamp = time.time()
        self._pending_disconnect = False

        self.OnConnectRequest = Event()
        self.OnDisconnect = Event()
        self.OnError = Event()
        self.OnMessage = Event()

        self._connection = connection.Connection(self)
        self._connection.OnMessage += self._Connection_OnMessage
        self._connection.OnDisconnect += self._Connection_OnDisconnect
        self._connection.OnError += self._Connection_OnError
        self._connection.OnConnectRequest += self._Connection_OnConnectRequest

    @property
    def address(self):
        return self._address

    @property
    def connected(self):
        return self._connected

    @property
    def in_bytes(self):
        return self._connection.in_bytes

    @property
    def is_server(self):
        return True

    @property
    def latency(self):
        return self._connection.latency

    @property
    def message_factory(self):
        return self.parent.message_factory

    @property
    def out_buffer_bytes(self):
        return self._connection.out_buffer_bytes

    @property
    def out_bytes(self):
        return self._connection.out_bytes

    @property
    def timeout(self):
        return self.parent.timeout

    @property
    def lastPacketSentAt(self):
        return self._connection.lastPacketSentAt

    def _Connection_OnMessage(self, sender, event_args):
        if not self._connected:
            self._pending_disconnect = True
        else:
            self.OnMessage(self, event_args)

    def _Connection_OnConnectRequest(self, sender, event_args):
        self._connected = self.OnConnectRequest(self, event_args)
        if self._connected is None:
            # No event handler bound, default action is to accept connection.
            self._connected = True
        return self._connected

    def _Connection_OnError(self, sender, error_string):
        self.OnError(self, error_string)

    def _Connection_OnDisconnect(self, sender, event_args):
        self.OnDisconnect(self, sender)

    def doRead(self, callback):
        self.parent.doRead(callback)

    def processInboundPacket(self, rawData):
        self._connection.processInboundPacket(rawData)

    def hasPacketsToSend(self):
        return self._connection.hasOutgoingPackets()

    def sendMessage(self, packet):
        '''
        Adds a packet to the outgoing buffer to be sent to the client.
        This does not set the in-order or reliable flags.
        packet is an instance of BasePacket.
        Returns the number of bytes added to the output buffer for
        sending this message (header + message bytes)
        '''
        if self._pending_disconnect:
            raise netshared.ServerError, \
                'Cannot sendMessage to a disconnecting peer'
        return self._connection.sendMessage(packet)

    def sendReliableMessage(self, packet):
        if self._pending_disconnect:
            raise netshared.ServerError, \
                'Cannot sendReliableMessage to a disconnecting peer'
        self._connection.sendReliableMessage(packet)

    def disconnect(self):
        '''
        Disconnect this peer. A Disconnected message will be sent to the client
        and this peer object will be deleted once the outgoing buffer for
        this connection has emptied.
        '''
        LOG.info('Sent Disconnected message to client')
        self._connection.sendMessage(
            self.parent.message_factory.getByName('Disconnected')())
        self._pending_disconnect = True

    def update(self):
        self._connection.update()
