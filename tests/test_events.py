# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

import legume.timing as time

import random
import unittest
import legume
from greenbar import GreenBarRunner
import logging

HOST = 'localhost'
ITERATIONS = 80

logger = logging.getLogger()

def getRandomPort():
    return random.randint(16000, 50000)


class ExampleMessage(legume.messages.BaseMessage):
    MessageTypeID = legume.messages.BASE_MESSAGETYPEID_USER+5
    MessageValues = {
        'message':'string 32'}

    def set_message_values_to_defaults(self):
        self.message.value = "Hello World!"


class TestEvents(unittest.TestCase):
    def setUp(self):
        logger.setLevel(logging.DEBUG)
        self.message_factory = legume.messages.MessageFactory()

        self.server = legume.Server(self.message_factory)
        self.client = legume.Client(self.message_factory)
        port = getRandomPort()
        self.server.listen((HOST, port))
        self.client.connect((HOST, port))

        self.test_passed = False
        self.peer_address = None
        self.client_peer = None
        self.call_count = 0
        logger.setLevel(logging.ERROR)


    def update(self):
        if self.server is not None:
            self.server.update()
        if self.client is not None:
            self.client.update()


    def testConnectRequestIsAccepted(self):
        def Server_OnConnectRequest(sender, event_args):
            return True

        def Client_OnConnectRequestAccepted(sender, event_args):
            self.test_passed = True

        self.client.OnConnectRequestAccepted += Client_OnConnectRequestAccepted
        self.server.OnConnectRequest += Server_OnConnectRequest

        for x in xrange(ITERATIONS):
            self.update()

        self.assertTrue(self.test_passed)
        self.assertTrue(self.client.connected)


    def testConnectRequestIsRejected(self):
        def Server_OnConnectRequest(sender, event_args):
            return False

        def Client_OnConnectRequestRejected(sender, event_args):
            self.test_passed = True

        self.client.OnConnectRequestRejected += Client_OnConnectRequestRejected
        self.server.OnConnectRequest += Server_OnConnectRequest

        for x in xrange(ITERATIONS):
            self.update()

        self.assertTrue(self.test_passed)
        self.assertFalse(self.client.connected)


    def testServerDisconnectsClient(self):
        logger.setLevel(logging.DEBUG)
        logging.info('@@@@@@@@@@@@ testServerDisconnectsClient @@@@@@@@@@@@')
        def Client_OnDisconnect(sender, event_args):
            self.test_passed = True

        def Server_OnConnectRequest(sender, event_args):
            self.peer_address = sender.address

        self.server.OnConnectRequest += Server_OnConnectRequest
        self.client.OnDisconnect += Client_OnDisconnect

        for x in xrange(ITERATIONS):
            self.update()

        self.server.disconnect(self.peer_address)

        for x in xrange(ITERATIONS):
            self.update()

        logging.info('^^^^^^^^^^^ testServerDisconnectsClient ^^^^^^^^^^^^^^^')
        logger.setLevel(logging.ERROR)
        self.assertTrue(self.test_passed)


    def testClientDisconnectsServer(self):
        def Server_OnConnectRequest(sender, event_args):
            self.peer_address = sender.address
            return True

        def Server_OnDisconnect(sender, event_args):
            self.assertEquals(self.peer_address, sender.address)
            self.test_passed = True

        self.server.OnDisconnect += Server_OnDisconnect
        self.server.OnConnectRequest += Server_OnConnectRequest

        for x in xrange(ITERATIONS):
            self.update()

        self.client.disconnect()

        for x in xrange(ITERATIONS):
            self.update()

        self.assertTrue(self.test_passed)


    def testClientDropsCausingErrorOnServer(self):
        def Server_OnError(sender, event_args):
            self.call_count += 1

        self.call_count = 0

        self.client.setTimeout(2.0)
        self.server.setTimeout(2.0)

        self.server.OnError += Server_OnError

        for x in xrange(ITERATIONS):
            self.update()

        self.client = None

        for x in xrange(ITERATIONS):
            time.sleep(0.1)
            self.update()

        self.assertEquals(self.call_count, 1)


    def testServerDropsCausingErrorOnClient(self):
        def Client_OnError(sender, event_args):
            self.test_passed = True

        self.client.setTimeout(2.0)
        self.server.setTimeout(2.0)

        self.client.OnError += Client_OnError

        for x in xrange(ITERATIONS):
            self.update()

        self.server = None

        for x in xrange(ITERATIONS):
            time.sleep(0.1)
            self.update()

        self.assertTrue(self.test_passed)


    def testSendMessageToServer(self):
        def Server_OnConnectRequest(sender, event_args):
            self.client_peer = sender
            return True

        def Server_OnMessage(sender, message):
            self.test_passed = (self.client_peer == sender)
            self.assertEquals(message.message.value, "HITHERE")
        self.message_factory.add(ExampleMessage)

        self.server.OnConnectRequest += Server_OnConnectRequest
        self.server.OnMessage += Server_OnMessage

        for x in xrange(ITERATIONS):
            self.update()

        example_message = ExampleMessage()
        example_message.message.value = "HITHERE"

        self.client.send_reliable_message(example_message)

        for x in xrange(ITERATIONS):
            self.update()

        self.assertTrue(self.test_passed)


    def testSendMessageToClient(self):
        def Client_OnMessage(sender, packet):
            self.test_passed = True
            self.assertEquals(packet.message.value, "HITHERE")
        self.message_factory.add(ExampleMessage)

        self.client.OnMessage += Client_OnMessage

        for x in xrange(ITERATIONS):
            self.update()

        example_message = ExampleMessage()
        example_message.message.value = "HITHERE"

        self.server.send_reliable_messageToAll(example_message)

        for x in xrange(ITERATIONS):
            self.update()

        self.assertTrue(self.test_passed)

logger = logging.getLogger()
fout = logging.FileHandler('test_events.log', 'w')
formatter = logging.Formatter('%(asctime)s [%(name)s %(levelname)s] - %(message)s')
fout.setFormatter(formatter)
logger.addHandler(fout)
logger.setLevel(logging.ERROR)

if __name__ == '__main__':
    from greenbar import GreenBarRunner
    tests = unittest.TestLoader().loadTestsFromTestCase(TestEvents)
    GreenBarRunner(verbosity=2).run(tests)