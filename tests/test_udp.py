# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

import sys
sys.path.append('..')
import unittest
import legume
import random

def getRandomPort():
    return random.randint(16000, 50000)

PORT = random.randint(16000, 26000)
import logging

# ========

class TestInstantiation(unittest.TestCase):
    def testClientCtor(self):
        c = legume.udp.Client()

    def testServerCtor(self):
        s = legume.udp.Server()

class TestConnectionSetup(unittest.TestCase):
    def testClientConnect(self):
        c = legume.udp.Client()
        c.connect(('localhost', getRandomPort()))

    def testServerListen(self):
        s = legume.udp.Server()
        s.listen(('', getRandomPort()))

class TestUpdate(unittest.TestCase):
    def testClientUpdate(Self):
        c = legume.udp.Client()
        c.update()

    def testServerUpdate(self):
        s = legume.udp.Server()
        s.update()

# ========

class TestClientState(unittest.TestCase):

    def setUp(self):
        self.client = legume.udp.Client()

    def testClientClosedStated(self):
        self.assertEquals(self.client.state, self.client.DISCONNECTED)

    def testClientBadPortException(self):
        def willfail():
            self.client.connect(('localhost', 'notaservice')) # Errored port number
        self.assertRaises(legume.exceptions.ArgumentError, willfail)

    def testClientConnectingState(self):
        self.client.connect(('localhost', getRandomPort()))
        self.assertEquals(self.client.state, self.client.CONNECTING)

    def testConnectReAttemptFails(self):
        def willfail():
            self.client.connect(('localhost', getRandomPort()))
            self.client.connect(('localhost', getRandomPort()))
        self.assertRaises(legume.udp.client.ClientError, willfail)

# ========

class TestServerState(unittest.TestCase):

    def setUp(self):
        self.server = legume.udp.Server()

    def testServerClosedState(self):
        self.assertEquals(self.server.state, self.server.DISCONNECTED)

    def testServerBadPortException(self):
        def willfail():
            self.server.listen(('', 'notaservice')) # Errored port number
        self.assertRaises(TypeError, willfail)

    def testServerListeningState(self):
        self.server.listen(('', getRandomPort()))
        self.assertEquals(self.server.state, self.server.LISTENING)

# ========

PACKET_HEADER_FORMAT = legume.udp.messages.BaseMessage.HEADER_FORMAT

class TestPacket(unittest.TestCase):

    def testConnectRequestPacketFormat(self):
        self.assertEquals(
            legume.udp.messages.ConnectRequest().get_header_format(),
            PACKET_HEADER_FORMAT)

    def testConnectRequestMessageValues(self):
        values = legume.udp.messages.ConnectRequest().get_message_values()
        values[1] = legume.udp.netshared.PROTOCOL_VERSION

        self.assertEquals(
            values,
            [legume.udp.messages.ConnectRequest.MessageTypeID,
            legume.udp.netshared.PROTOCOL_VERSION])


class TestPacket1(legume.udp.messages.BaseMessage):
    MessageTypeID = legume.udp.messages.BASE_MESSAGETYPEID_USER+1
    def __init__(self):
        legume.udp.messages.BaseMessage.__init__(self,
            legume.udp.messages.MessageValue(
                'message', 'string', 'Hello World!', max_length=32))

class TestTestPacket1NormalUsage(unittest.TestCase):

    def setUp(self):
        self.tp = TestPacket1()

    def testTestPacket1_1(self):
        self.assertEquals(
            self.tp.get_message_values(),
            [TestPacket1.MessageTypeID, 'Hello World!'])

    def testTestPacket1Value(self):
        self.assertEquals(
            self.tp.message.value, 'Hello World!')

    def testTestPacket1ValueType(self):
        self.assertEquals(
            self.tp.message.typename, 'string')

    def testTestPacket1ValueFormatString(self):
        self.assertEquals(
            self.tp.message.get_format_string(), '32s')

    def testTestPacket1PacketFormat(self):
        self.assertEquals(
            self.tp.get_message_format(),
            PACKET_HEADER_FORMAT + '32s')

    def testGetPacketString(self):
        self.tp.get_packet_bytes()

    def testLongValueRaisesException(self):
        def setLongValue():
            self.tp.message.value = "ThisMessageIsLongerThan32Characters."

        self.assertRaises(
            legume.udp.messages.MessageError,
            setLongValue)

# ========

# Tests connection of clients to server

class TestClientConnectionToServer(unittest.TestCase):
    def testRunSingleClient(self):
        PORT = getRandomPort()
        c = legume.udp.Client()
        s = legume.udp.Server()

        s.listen(('', PORT))
        c.connect(('localhost', PORT))

        for i in xrange(100):
            c.update()
            s.update()

        self.assertTrue(c.connected)

    def testRunTwoClients(self):
        PORT = getRandomPort()
        c1 = legume.udp.Client()
        c2 = legume.udp.Client()
        s = legume.udp.Server()

        s.listen(('', PORT))
        c1.connect(('localhost', PORT))
        c2.connect(('localhost', PORT))

        for i in xrange(100):
            c1.update()
            c2.update()
            s.update()

        self.assertTrue(c1.connected)
        self.assertTrue(c2.connected)


# ========

# Test connection request accept/reject mechanism

class TestConnectRequest(unittest.TestCase):
    def setUp(self):
        self.serverPort = getRandomPort()
        self.server = legume.udp.Server()
        self.client = legume.udp.Client()

    def connectEndpoints(self):
        self.server.listen(('', self.serverPort))
        self.client.connect(('localhost', self.serverPort))

    def performUpdateLoop(self):
        self.connectEndpoints()

        i = 0
        while i < 100:
            self.server.update()
            self.client.update()
            i += 1

    def testServerDoesNotAcceptConnection(self):
        '''
        The server should not accept the connection and the clients
        state at the end of the update loop should be ERRORED.
        '''
        def rejectConnection(endpoint, packet):
            print('Rejecting connection.')
            return False

        self.server.OnConnectRequest += rejectConnection
        self.performUpdateLoop()
        self.assertTrue(self.client.errored)

    def testServerShouldAcceptConnection(self):
        '''
        The server should accept the clients connection request.
        At the end of this update loop the clients status should be
        CONNECTED.
        '''
        def acceptConnection(endpoint, packet):
            print('Accepting connection.')
            return True

        self.server.OnConnectRequest += acceptConnection
        self.performUpdateLoop()
        self.assertTrue(self.client.connected)


class TestGracefulDisconnect(unittest.TestCase):
    '''
    Server should issue a disconnect packet to the client causing
    both ends of the connection to close gracefully.
    '''
    def setUp(self):
        self.serverPort = getRandomPort()
        self.server = legume.udp.Server()
        self.client = legume.udp.Client()
        self.got_disconnect_message = False

    def connectEndpoints(self):
        self.server.listen(('', self.serverPort))
        self.client.connect(('localhost', self.serverPort))

    def performUpdateLoop(self):
        self.peer_address = None

        def Server_OnConnectRequest(endpoint, packet):
            self.peer_address = endpoint.address
            return True

        def Client_OnDisconnect(sender, event_args):
            self.got_disconnect_message = True

        self.server.OnConnectRequest += Server_OnConnectRequest
        self.client.OnDisconnect += Client_OnDisconnect

        i = 0
        while i < 200:
            self.server.update()
            self.client.update()
            i += 1

            if i == 50:
                self.server.disconnect(self.peer_address)

    def testServerDisconnectsClient(self):
        self.connectEndpoints()
        self.performUpdateLoop()
        self.assertTrue(self.client.disconnected)
        self.assertTrue(self.got_disconnect_message)


# ========

class MessagePacketOldFormat(legume.udp.messages.BaseMessage):
    MessageTypeID = legume.udp.messages.BASE_MESSAGETYPEID_USER+3
    def __init__(self):
        legume.udp.messages.BaseMessage.__init__(self,
            legume.udp.messages.MessageValue(
                'message', 'string', 'Hello World!', max_length=32))

class MessagePacket(legume.udp.messages.BaseMessage):
    MessageTypeID = legume.udp.messages.BASE_MESSAGETYPEID_USER+3
    MessageValues = {
        'message' : 'string 32'
        }

class TestServerToClientMessage(unittest.TestCase):
    def setUp(self):
        self.mf = legume.udp.messages.MessageFactory()
        self.mf.add(MessagePacket)
        self.serverPort = getRandomPort()
        self.server = legume.udp.Server(self.mf)
        self.client = legume.udp.Client(self.mf)
        self.peer_address = None
        self.message_to_send = "WHY HELLO THERE!"
        self.received_message = None

    def Server_OnConnectRequest(self, peer, packet):
        print('Got connection request')
        self.peer_address = peer.address
        return True

    def Client_OnMessage(self, sender, message):
        if self.received_message is not None:
            raise Exception, 'Tear in the fabric of space and time!'
        self.received_message = message.message.value
        print('Got message: %s' % self.received_message)


    def connectEndpoints(self):
        self.server.listen(('', self.serverPort))
        self.client.connect(('localhost', self.serverPort))

        self.server.OnConnectRequest += self.Server_OnConnectRequest
        self.client.OnMessage += self.Client_OnMessage

    def performUpdateLoop(self):

        sent_packet = False

        i = 0
        while i < 200:

            if (not sent_packet) and (self.peer_address is not None):
                p = MessagePacket()
                p.message.value = self.message_to_send
                self.server.get_peer_by_address(self.peer_address).send_message(p)
                sent_packet = True
                print('Sent message from Server to Client')

            self.server.update()
            self.client.update()

            i += 1

    def testMessagePass(self):
        print('Start of testMessagePass')
        self.connectEndpoints()
        self.performUpdateLoop()
        self.assertEquals(self.message_to_send, self.received_message)



class TestPacket2(legume.udp.messages.BaseMessage):
    MessageTypeID = legume.udp.messages.BASE_MESSAGETYPEID_USER+2
    def __init__(self):
        legume.udp.messages.BaseMessage.__init__(self)
        self.addValue('message', 'string', 'Hello World!', max_length=32)

class TestPacket2SameID(legume.udp.messages.BaseMessage):
    MessageTypeID = legume.udp.messages.BASE_MESSAGETYPEID_USER+2
    def __init__(self):
        legume.udp.messages.BaseMessage.__init__(self)
        self.addValue('message', 'string', 'Hello World!', max_length=32)

class TestMessageFactory(unittest.TestCase):
    def setUp(self):
        self.mf = legume.udp.messages.MessageFactory()

    def testMessageFactoryHasBaseMessagesByDefault(self):
        for pname, pclass in legume.udp.messages.messages.iteritems():
            self.assertEquals(self.mf.get_by_name(pname), pclass)

    def testMessageFactoryAddTestPacket2(self):
        self.mf.add(TestPacket2)
        self.assertEquals(self.mf.get_by_name('TestPacket2'), TestPacket2)

    def testMessageFactoryCantShareIDs(self):
        def willfail():
            self.mf.add(TestPacket2)
            self.mf.add(TestPacket2SameID)
        self.assertRaises(legume.udp.messages.MessageError, willfail)

    def testMessageFactoryCanAddMultiplePackets(self):
        self.mf.add(TestPacket1)
        self.mf.add(TestPacket2)

    def testMessageFactoryCantAddPacketTwice(self):
        def willfail():
            self.mf.add(TestPacket2)
            self.mf.add(TestPacket2)
        self.assertRaises(legume.udp.messages.MessageError, willfail)

    def testMessageFactoryNotJustReturningRubbish(self):
        self.mf.add(TestPacket2)
        def willfail():
            self.mf.get_by_name('ThisPacketIsMakeBelieve')
        self.assertRaises(legume.udp.messages.MessageError, willfail)

    def testMessageFactoryGetById(self):
        self.mf.add(TestPacket2)
        self.assertEquals(
            self.mf.get_by_id(TestPacket2.MessageTypeID).MessageTypeID,
            TestPacket2.MessageTypeID)

    def testMessageFactoryGetByIdBadId(self):
        def willfail():
            self.mf.get_by_id(423984723)
        self.assertRaises(legume.udp.messages.MessageError, willfail)

    def testGetBuiltinPacketById(self):
        self.assertEquals(
            legume.udp.messages.ConnectRequest,
            self.mf.get_by_id(legume.udp.messages.ConnectRequest.MessageTypeID))

class TestDisconnectAll(unittest.TestCase):
    def setUp(self):
        self.port = getRandomPort()
        self.server = legume.udp.Server()
        self.client1 = legume.udp.Client()
        self.client2 = legume.udp.Client()
        self.on_disconnect_count = 0

        self.client1.OnDisconnect += self.Client_OnDisconnect
        self.client2.OnDisconnect += self.Client_OnDisconnect

        self.server.listen(('', self.port))
        self.client1.connect(('localhost', self.port))
        self.client2.connect(('localhost', self.port))

    def Client_OnDisconnect(self, sender, event):
        self.on_disconnect_count += 1

    def update(self):
        self.server.update()
        self.client1.update()
        self.client2.update()

    def testDisconnectAll(self):
        for x in xrange(100):
            self.update()

        self.assertTrue(self.client1.connected)
        self.assertTrue(self.client2.connected)
        self.assertEquals(self.server.peercount, 2)

        self.server.disconnect_all()

        for x in xrange(100):
            self.update()

        self.assertEquals(self.on_disconnect_count, 2)

        self.assertEquals(self.server.peercount, 0)




# ========

if __name__ == '__main__':
    from greenbar import GreenBarRunner
    logging.basicConfig(level=logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    GreenBarRunner(verbosity=2).run(suite)