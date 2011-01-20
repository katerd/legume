# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

'''A `Client` manages the connection to a `Server` instance elsewhere.

Creating an instance of a `Client` and connecting to a server is done
as shown in the minimalist example below::

    client = Client()
    # Server is running on localhost port 9000
    client.connect(('localhost', 9000))

    # This loop ensures that .update() is called.
    while True:
        client.update()
        # Add a small time delay to prevent pegging the CPU.
        time.sleep(0.0001)

The `Client` has a number of events that can be hooked into that provide
notifications of data sent from the server and state changes. An event
consists of the sender and the argument(in the example below, this
is the message), eg::

    def my_message_handler(sender, message):
        print "The greeting reads: %s" % message.greeting.value

    my_client.OnMessage += my_message_handler

For the `Client.OnMessage` handler example above the argument part of the
event received is a re-assembled instance of the message that was sent, and
the greeting field in the message is obtained via
the fields `value` attribute.

* `Client.OnConnectRequestAccepted` - Fired when a `Client.connect` request
    has been responded to by the server allowing the connection.
* `Client.OnConnectRequestRejected` - Fired when a `Client.connect` request
    has been responded to by the server deneying the connection.
* `Client.OnMessage` - Fired when a message is receieved from the server.
    See above example.
* `Client.OnError` - An error has occured. The event argument is a string
    detailing the error.
* `Client.OnDisconnect` - The connection was gracefully closed by the
    Server. If the connection was severed due to a time-out, the
    `Client.OnError` event would fire.

'''

__docformat__ = 'restructuredtext'

import messages
import netshared
import connection
import logging
from legume.nevent import Event, NEventError

from legume.exceptions import ClientError

class Client(netshared.NetworkEndpoint):

    _log = logging.getLogger('legume.client')

    def __init__(self, message_factory=messages.message_factory):
        '''
        Create a Client endpoint. A Client is initially in the closed state
        until a call to `connect`.

        A messages factory is required to assemble and disassemble messages for
        pushing down the intertubes to the server endpoint. If a
        message_factory is not explicitly specified then the global
        message_factory will be used.

        :Parameters:
            message_factory : `MessageFactory`
                A message factory.
        '''
        netshared.NetworkEndpoint.__init__(self, message_factory)
        self._address = None
        self._connection = None
        self._disconnecting = False

        self._OnConnectRequestRejected = Event()
        self._OnMessage = Event()
        self._OnConnectRequestAccepted = Event()
        self._OnError = Event()
        self._OnDisconnect = Event()


    # ------------- Properties -------------


    @property
    def connected(self):
        '''
        Returns True if this endpoint's state is `CONNECTED`.
        '''
        return self._state == self.CONNECTED

    @property
    def disconnected(self):
        '''
        Returns True if this endpoint's state is `DISCONNECTED`.
        '''
        return self._state == self.DISCONNECTED

    @property
    def errored(self):
        '''
        Returns True if this endpoint's state is `ERRORED`.
        '''
        return self._state == self.ERRORED

    @property
    def is_server(self):
        '''Returns false.'''
        return False

    @property
    def latency(self):
        if self._connection is not None:
            return self._connection.latency
        else:
            return 0

    @property
    def out_buffer_bytes(self):
        if self._connection is not None:
            return self._connection.out_buffer_bytes
        else:
            return 0

    @property
    def pending_acks(self):
        # TODO: implement
        return 0

    @property
    def in_bytes(self):
        if self._connection is not None:
            return self._connection.in_bytes
        else:
            return 0

    @property
    def out_bytes(self):
        if self._connection is not None:
            return self._connection.out_bytes
        else:
            return 0

    @property
    def in_packets(self):
        # TODO: implement
        return 0

    @property
    def out_packets(self):
        # TODO: implement
        return 0

    @property
    def keepalive_count(self):
        if self._connection is not None:
            return self._connection.keepalive_count
        else:
            return 0

    @property
    def reorder_queue(self):
        if self._connection is not None:
            return self._connection.reorder_queue
        else:
            return 0

    # ------------- Public Methods -------------

    def connect(self, address):
        '''
        Initiate a connection to the server at the specified address.

        This method will put the socket into the `CONNECTING` state. If a
        connection is already established a ClientError exception is raised.

        :Parameters:
            address : (host, port)
                Host address. If the port is invalid an ArgumentError
                exception will be raised.
        '''
        if self.isActive():
            raise ClientError(
                'Client cannot reconnect in a CONNECTING or CONNECTED state')
        if not netshared.isValidPort(address[1]):
            raise ArgumentError(
                '%s is not a valid port' % str(address[1]))
        self._createSocket()
        self._connectSocket(address)
        self._address = address

        self._connection = connection.Connection(self)

        self._connection.OnConnectRequestAccepted += \
            self._Connection_OnConnectRequestAccepted
        self._connection.OnConnectRequestRejected += \
            self._Connection_OnConnectRequestRejected
        self._connection.OnError += self._Connection_OnError
        self._connection.OnDisconnect += self._Connection_OnDisconnect
        self._connection.OnMessage += self._Connection_OnMessage

        request_message = self.message_factory.getByName('ConnectRequest')()
        request_message.protocol.value = netshared.PROTOCOL_VERSION
        self._sendReliableMessage(request_message)
        self._state = self.CONNECTING


    def disconnect(self):
        '''
        Gracefully disconnect from the host. A disconnection packet is
        sent to the server upon calling the .update() method. The connection
        status of the class instance will not changed to  `DISCONNECTED`
        until .update() is called.
        '''
        if self._connection is not None:
            self._connection.sendMessage(
                self.message_factory.getByName('Disconnected')())
            self._disconnecting = True


    def sendMessage(self, message):
        '''
        Send a message to the server. The message is added to the output buffer.
        To flush the output buffer call the .update() method. If the client
        is not connected to the server a `ClientError` exception is raised.

        :Parameters:
            message : `BaseMessage`
                The message to be sent
        '''
        if self._state == self.CONNECTED:
            return self._sendMessage(message)
        else:
            raise ClientError, 'Cannot send packet - not connected'


    def sendReliableMessage(self, message):
        '''
        Send a message to the server with guaranteed delivery. If the
        client is not connected to the server a `ClientError` exception
        is raised.

        :Parameters:
            message : `BaseMessage`
                The message to be sent
        '''
        if self._state == self.CONNECTED:
            return self._sendReliableMessage(message)
        else:
            raise ClientError, 'Cannot send message - not connected'


    def update(self):
        '''
        This method should be called frequently to process incoming data,
        send outgoing data, and raise events.
        '''
        self._log.debug('update')
        if self._state in [self.CONNECTING, self.CONNECTED]:
            self._log.debug('connection.update')
            self._connection.update()

        if self._disconnecting and not self._connection.hasOutgoingPackets():
            self._disconnect(raise_event=False)


    # ------------- Private Methods -------------


    def _sendMessage(self, message):
        return self._connection.sendMessage(message)


    def _sendReliableMessage(self, message):
        return self._connection.sendReliableMessage(message)


    def _disconnect(self, raise_event=True):
        self._state = self.DISCONNECTED
        self._shutdownSocket()
        self._disconnecting = False
        if raise_event:
            self.OnDisconnect(self, None)


    # ------------- Events -------------


    def _getOnConnectRequestRejected(self):
        return self._OnConnectRequestRejected
    def _setOnConnectRequestRejected(self, event):
        if isinstance(event, Event):
            self._OnConnectRequestRejected = event
        else:
            raise NEventError, 'Event must subclass nevent.Event'
    OnConnectRequestRejected = property(
        _getOnConnectRequestRejected, _setOnConnectRequestRejected)

    def _getOnMessage(self):
        return self._OnMessage
    def _setOnMessage(self, event):
        if isinstance(event, Event):
            self._OnMessage = event
        else:
            raise NEventError, 'Event must subclass nevent.Event'
    OnMessage = property(
        _getOnMessage, _setOnMessage)

    def _getOnConnectRequestAccepted(self):
        return self._OnConnectRequestAccepted
    def _setOnConnectRequestAccepted(self, event):
        if isinstance(event, Event):
            self._OnConnectRequestAccepted = event
        else:
            raise NEventError, 'Event must subclass nevent.Event'
    OnConnectRequestAccepted = property(
        _getOnConnectRequestAccepted, _setOnConnectRequestAccepted)

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


    # ------------- Connection Event Handlers -------------


    def _Connection_OnConnectRequestRejected(self, sender, event_args):
        self._state = self.ERRORED
        self._shutdownSocket()
        self.OnConnectRequestRejected(self, event_args)

    def _Connection_OnMessage(self, sender, message):
        self.OnMessage(self, message)

    def _Connection_OnConnectRequestAccepted(self, sender, event_args):
        self._state = self.CONNECTED
        self.OnConnectRequestAccepted(self, event_args)

    def _Connection_OnError(self, sender, error_string):
        self._state = self.ERRORED
        self._shutdownSocket()
        self.OnError(self, error_string)

    def _Connection_OnDisconnect(self, sender, event_args):
        self._disconnect()

