# legume. Copyright 2009 Dale Reidy. All rights reserved. See LICENSE for details.

import sys

import legume.timing as time
time.test_mode(True)

import random
import unittest
import legume
from greenbar import GreenBarRunner
import logging

HOST = '127.0.0.1'
ITERATIONS = 100

def getRandomPort():
    import random
    return random.randint(16000, 50000)

class TestClientMetricsInterface(unittest.TestCase):
    def setUp(self):
        self.client = legume.udp.Client()

    def testReorderQueue(self):
        self.assert_(self.client.reorder_queue >= 0)

    def testBufferBytesInterface(self):
        self.assert_(self.client.out_buffer_bytes >= 0)

    def testPendingAcksInterface(self):
        self.assert_(self.client.pending_acks >= 0)

    def testTransmitBytesInterface(self):
        self.assert_(self.client.in_bytes >= 0)
        self.assert_(self.client.out_bytes >= 0)

    def testPacketsInterface(self):
        self.assert_(self.client.in_packets >= 0)
        self.assert_(self.client.out_packets >= 0)

    def testKeepAliveInterface(self):
        self.assert_(self.client.keepalive_count >= 0)

class ExampleMessage(legume.udp.messages.BaseMessage):
    MessageTypeID = legume.udp.messages.BASE_MESSAGETYPEID_USER+1
    MessageValues = {
        'param1':'int',
        'param2':'varstring'}

class TestMetrics(unittest.TestCase):
    def setUp(self):
        self.port = getRandomPort()
        self.message_factory = legume.udp.messages.MessageFactory()
        self.message_factory.add(ExampleMessage)
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

    def testClientOut(self):
        self.wait_for_client_connection()
        peer = self.server.peers[0]

        expected_xfer = 0

        for x in xrange(ITERATIONS):
            msg = ExampleMessage()
            msg.param1.value = 100
            msg.param2.value = "example_message"
            msg_length = len(msg.getPacketBytes())

            out_buffer_bytes = self.client.sendMessage(msg)
            expected_xfer += len(msg.getPacketBytes())
            # can't directly compare due to header
            self.assert_(self.client.out_buffer_bytes >= msg_length)

            # buffer *must* increase in size after sending another message
            expected_xfer += self.client.sendMessage(msg)

            self.assert_(self.client.out_buffer_bytes > msg_length)

            self.update()
            self.update()

            self.assert_(self.client.out_bytes > expected_xfer)
            self.assert_(peer.in_bytes > expected_xfer)

    def testServerOut(self):
        self.wait_for_client_connection()
        peer = self.server.peers[0]

        msg = ExampleMessage()
        msg.param1.value = 100
        msg.param2.value = "example_message"
        msg_length = len(msg.getPacketBytes())

        peer.sendMessage(msg)

        # can't directly compare due to header
        out_buffer_bytes = peer.out_buffer_bytes
        self.assert_(peer.out_buffer_bytes >= msg_length)

        # buffer *must* increase in size after sending another message
        peer.sendMessage(msg)
        self.assert_(peer.out_buffer_bytes > out_buffer_bytes)

        self.update()
        self.update()

        self.assert_(peer.out_bytes > (msg_length*2))
        self.assert_(self.client.in_bytes > (msg_length*2))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    GreenBarRunner(verbosity=2).run(suite)