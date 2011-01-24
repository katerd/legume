# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

__docformat__ = 'restructuredtext'

import logging
import netshared
import messages
from nevent import Event, NEventError
from servicelocator import Service

class Server(netshared.NetworkEndpoint):
    '''
    A server. To allow network clients to communicate with this class
    call listen() with a network address then periodically call update()
    to ensure data is kept flowing and connects/disconnects are handled.
    '''
    _log = logging.getLogger('legume.server')

    def __init__(self, message_factory=messages.message_factory):
        '''
        Create an instance of a new Server endpoint. Use the message_factory
        parameter to specify an alternative to the global messages.message_factory
        instance::

            mf = legume.udp.messages.MessageFactory()
            server = legume.udp.Server(message_factory=mf)
        '''
        netshared.NetworkEndpoint.__init__(self, message_factory)
        self._peers = {}
        self._dead_peers = [] # List of peers (by address) to be removed
        self._in_update = False

        self._OnConnectRequest = Event()
        self._OnDisconnect = Event()
        self._OnError = Event()
        self._OnMessage = Event()

    # ------------- Properties -------------

    @property
    def peercount(self):
        '''Number of connected peers.'''
        return sum(
            1 for peer in self._peers.itervalues()
            if peer.connected)

    @property
    def peers(self):
        '''A list of connected peers.'''
        return [
            peer for peer in self._peers.itervalues()
            if peer.connected]

    # ------------- Public Methods -------------

    def disconnect(self, peer_address):
        '''Disconnect a peer by specifying their address.
        Equivalent to::

            server.get_peer_by_address(peer_address).disconnect()
        '''
        self.get_peer_by_address(peer_address).disconnect()

    def disconnect_all(self):
        '''Disconnect all connected clients'''
        for peer in self._peers.itervalues():
            peer.disconnect()

    def get_peer_by_address(self, peer_address):
        '''Obtain a ServerPeer instance by specifying the peer's address'''
        return self._peers[peer_address]

    def listen(self, address):
        '''Begin listening for incoming connections.
        address is a tuple of the format (hostname, port)
        This method change the class state to LISTENING::

            # Begin listening on port 4000 on all IP interfaces
            server = legume.udp.Server()
            server.listen(('', 4000))
        '''
        if self.is_active():
            raise netshared.ServerError(
                'Server cannot listen whilst in a LISTENING state')
        self._create_socket()
        self._bind_socket(address)
        self._address = address
        self._state = self.LISTENING

    def update(self):
        '''Pumps buffers and dispatches events. Call regularly to ensure
        buffers do not overfill or connections time-out::

            server = legume.udp.Server()
            server.listen(('', 4000))

            while True:
                server.update()
                # Other update tasks here..
                time.sleep(0.001)
        '''
        self.do_read(self._on_socket_data)

        for peer in self._peers.itervalues():
            peer.update()

            if peer._pending_disconnect and not peer.has_packets_to_send():
                self._dead_peers.append(peer)

        self._removePeers()

    def send_messageToAll(self, message):
        '''Send a non-reliable packet to all connected peers.
        packet is an instance of a legume.message.BaseMessage subclass::

            message = ExampleMessage()
            message.chat_message.value = "Hello!"
            message.sender.value = "@X3"
            server.send_messageToAll(message)
        '''
        for peer in self._peers.itervalues():
            peer.send_message(message)

    def send_reliable_messageToAll(self, message):
        '''Send a reliable message to all connected peers. message is an
        instance of a legume.udp.message.BaseMessage subclass.
        '''
        for peer in self._peers.itervalues():
            peer.send_reliable_message(message)

    # ------------- Private Methods -------------

    def _on_socket_data(self, data, addr):
        self._log.debug(
            'Got data %s bytes in length from %s' %
            (str(len(data)), str(addr)))

        if not addr in self._peers:
            new_peer = Service('Peer', {'parent':self, 'address':addr})
            self._peers[addr] = new_peer

            new_peer.OnDisconnect += self._Peer_OnDisconnect
            new_peer.OnError += self._Peer_OnError
            new_peer.OnMessage += self._Peer_OnMessage
            new_peer.OnConnectRequest += self._Peer_OnConnectRequest

        self._peers[addr].process_inbound_packet(data)

    def _removePeers(self):
        for dead_peer in self._dead_peers:
            del self._peers[dead_peer.address]
        self._dead_peers = []

    # ------------- Events -------------

    def _getOnMessage(self):
        return self._OnMessage
    def _setOnMessage(self, event):
        if isinstance(event, Event):
            self._OnMessage = event
        else:
            raise NEventError, 'Event must subclass nevent.Event'
    OnMessage = property(
        _getOnMessage, _setOnMessage)

    def _getOnConnectRequest(self):
        return self._OnConnectRequest
    def _setOnConnectRequest(self, event):
        if isinstance(event, Event):
            self._OnConnectRequest = event
        else:
            raise NEventError, 'Event must subclass nevent.Event'
    OnConnectRequest = property(
        _getOnConnectRequest, _setOnConnectRequest)

    def _getOnError(self):
        return self._OnError
    def _setOnError(self, event):
        if isinstance(event, Event):
            self._OnError = event
        else:
            raise NEventError, 'Event must subclass nevent.Event'
    OnError = property(
        _getOnError, _setOnError)

    def _getOnDisconnect(self):
        return self._OnDisconnect
    def _setOnDisconnect(self, event):
        if isinstance(event, Event):
            self._OnDisconnect = event
        else:
            raise NEventError, 'Event must subclass nevent.Event'
    OnDisconnect = property(
        _getOnDisconnect, _setOnDisconnect)

    # ------------- Peer Event Handlers -------------

    def _Peer_OnConnectRequest(self, peer, event_args):
        return self.OnConnectRequest(peer, event_args)

    def _Peer_OnError(self, peer, error_string):
        self._dead_peers.append(peer)
        self.OnError(peer, error_string)

    def _Peer_OnMessage(self, peer, message):
        self.OnMessage(peer, message)

    def _Peer_OnDisconnect(self, peer, event_args):
        self.OnDisconnect(peer, None)