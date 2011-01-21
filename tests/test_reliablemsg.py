# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

import legume.timing as time
time.test_mode(True)

import random
import unittest
import legume
from greenbar import GreenBarRunner
import logging

HOST = '127.0.0.1'
MESSAGE_COUNT = 40

def getRandomPort():
    import random
    return random.randint(16000, 50000)

class SendMetrics(object):
    def __init__(self):
        self.sent = 0
        self.recv = 0

class ReliableMessage(legume.udp.messages.BaseMessage):
    MessageTypeID = legume.udp.messages.BASE_MESSAGETYPEID_USER+10
    MessageValues = {
        'param1':'int'}

class ChaffMessage(legume.udp.messages.BaseMessage):
    MessageTypeID = legume.udp.messages.BASE_MESSAGETYPEID_USER+11
    MessageValues = {
        'str':'varstring'}

class TestReliableMessage(unittest.TestCase):
    def setUp(self):
        self.port = getRandomPort()
        self.message_factory = legume.udp.messages.MessageFactory()
        self.message_factory.add(ReliableMessage)
        self.message_factory.add(ChaffMessage)
        self.server = legume.udp.Server(self.message_factory)
        self.client = legume.udp.Client(self.message_factory)

        self.server.listen((HOST, self.port))
        self.client.connect((HOST, self.port))
        self.wait_for_client_connection()

    def wait_for_client_connection(self):
        while not self.client.connected:
            self.update()

    def update(self):
        if self.server is not None:
            self.server.update()
        if self.client is not None:
            self.client.update()
        time.sleep(0.001)

    def testServerSendingReliableMessagesToClient(self):
        self.recv_count = 0
        self.send_count = 0

        def Client_OnMessage(sender, message):
            self.recv_count += 1
        self.client.OnMessage += Client_OnMessage

        for x in xrange(MESSAGE_COUNT):
            msg = ReliableMessage()
            msg.param1.value = x
            self.server.send_reliable_messageToAll(msg)
            self.send_count += 1
            self.update()

        self.assertEquals(self.recv_count, self.send_count)

    def testClientSendingReliableMessagesToServer(self):
        self.recv_count = 0
        self.send_count = 0

        def Server_OnMessage(sender, message):
            self.recv_count += 1

        self.server.OnMessage += Server_OnMessage

        for x in xrange(MESSAGE_COUNT):
            msg = ReliableMessage()
            msg.param1.value = x
            self.client.send_reliable_message(msg)
            self.send_count += 1
            self.update()
        self.update()

        self.assertEquals(self.recv_count, self.send_count)

    def testBidirectionalReliableMessagePassing(self):
        self.server_to_client = SendMetrics()
        self.client_to_server = SendMetrics()

        def Client_OnMessage(sender, message):
            self.server_to_client.recv += 1
        self.client.OnMessage += Client_OnMessage

        def Server_OnMessage(sender, message):
            self.client_to_server.recv += 1
        self.server.OnMessage += Server_OnMessage

        for x in xrange(MESSAGE_COUNT):
            msg = ReliableMessage()
            msg.param1.value = x
            self.client.send_reliable_message(msg)
            self.client_to_server.sent += 1
            self.server.send_reliable_messageToAll(msg)
            self.server_to_client.sent += 1
            self.update()
        self.update()

        self.assertEquals(
            self.server_to_client.sent,
            self.server_to_client.recv)

        self.assertEquals(
            self.client_to_server.sent,
            self.client_to_server.recv)

    def testClientSendingMixedModeMessagesToServer(self):
        self.recv_count = 0
        self.send_count = 0

        def Server_OnMessage(sender, message):
            # ignore chaff messages
            if self.message_factory.is_a(message, 'ReliableMessage'):
                self.recv_count += 1

        self.server.OnMessage += Server_OnMessage

        for x in xrange(MESSAGE_COUNT):
            msg = ReliableMessage()
            msg.param1.value = x
            self.client.send_reliable_message(msg)
            self.send_count += 1

            chaff = ChaffMessage()
            chaff.str.value = "A" * random.randint(1, 1000)
            self.client.send_message(chaff)

            self.update()
        self.update()

        self.assertEquals(self.recv_count, self.send_count)

    def testServerSendingMixedModeMessagesToClient(self):
        self.recv_count = 0
        self.send_count = 0

        def Client_OnMessage(sender, message):
            # ignore chaff messages
            if self.message_factory.is_a(message, 'ReliableMessage'):
                self.recv_count += 1

        self.client.OnMessage += Client_OnMessage

        for x in xrange(MESSAGE_COUNT):
            msg = ReliableMessage()
            msg.param1.value = x
            self.server.send_reliable_messageToAll(msg)
            self.send_count += 1

            chaff = ChaffMessage()
            chaff.str.value = "A" * random.randint(1, 1000)
            self.server.send_messageToAll(chaff)

            self.update()
        self.update()

        self.assertEquals(self.recv_count, self.send_count)

    def testBidirectionalMixedModeMessagePassing(self):
        self.server_to_client = SendMetrics()
        self.client_to_server = SendMetrics()

        def Client_OnMessage(sender, message):
            if self.message_factory.is_a(message, 'ReliableMessage'):
                self.server_to_client.recv += 1
        self.client.OnMessage += Client_OnMessage

        def Server_OnMessage(sender, message):
            if self.message_factory.is_a(message, 'ReliableMessage'):
                self.client_to_server.recv += 1
        self.server.OnMessage += Server_OnMessage

        for x in xrange(MESSAGE_COUNT):
            msg = ReliableMessage()
            msg.param1.value = x
            self.client.send_reliable_message(msg)
            self.client_to_server.sent += 1
            self.server.send_reliable_messageToAll(msg)
            self.server_to_client.sent += 1

            chaff = ChaffMessage()
            chaff.str.value = "A" * random.randint(1, 1000)
            self.client.send_message(chaff)

            self.server.send_messageToAll(chaff)

            self.update()
        self.update()

        self.assertEquals(
            self.server_to_client.sent,
            self.server_to_client.recv)

        self.assertEquals(
            self.client_to_server.sent,
            self.client_to_server.recv)

if __name__ == '__main__':
    mytests = unittest.TestLoader().loadTestsFromTestCase(TestReliableMessage)
    GreenBarRunner(verbosity=2).run(mytests)