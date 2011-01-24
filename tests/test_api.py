# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

import logging
import sys
import unittest
import legume
from legume.exceptions import *

class ExampleMessage(legume.messages.BaseMessage):
    MessageTypeID = 43011
    MessageValues = {'int':'int'}

class TestClientApi(unittest.TestCase):
    def setUp(self):
        print legume
        self.client = legume.Client()

    def testConnectWithOneTupleArg(self):
        def fails():
            self.client.connect(('localhost',))
        self.assertRaises(ArgumentError, fails)

    def testConnectWithInvalidTupleArg(self):
        def fails():
            self.client.connect(('localhost', 'bbbbb'))
        self.assertRaises(ArgumentError, fails)

    def testConnectWithInvalidArg(self):
        def fails():
            self.client.connect('localhost')
        self.assertRaises(ArgumentError, fails)

    def testConnectAcceptsValidArgument(self):
        # low port
        self.client.connect(('localhost', 881))

    def testConnectAcceptsValidArgument2(self):
        # hostname with high port
        self.client.connect(('localhost', 54001))

    def testConnectAcceptsValidArgument3(self):
        # ip with high port
        self.client.connect(('127.0.0.1', 54001))

    def testAcceptsPortAsString(self):
        self.client.connect(('127.0.0.1', '80'))

    def testDoubleConnectCausesFailure(self):
        def fails():
            self.client.connect(('127.0.0.1', 8000))
            self.client.connect(('127.0.0.1', 8000))
        self.assertRaises(ClientError, fails)

    def testDoubleDisconnectIsIgnored(self):
        self.client.disconnect()
        self.client.disconnect()

    def testCannotSendPacketInDisconnectedState(self):
        def fails():
            self.client.send_message(ExampleMessage())
        self.assertRaises(ClientError, fails)

    def testCannotSendReliablePacketInDisconnectedState(self):
        def fails():
            self.client.send_reliable_message(ExampleMessage())
        self.assertRaises(ClientError, fails)

    def testUpdateDoesntCauseErrorInUnconnectedState(self):
        self.client.update()


if __name__ == '__main__':
    from greenbar import GreenBarRunner
    logging.basicConfig(level=logging.ERROR)
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    GreenBarRunner(verbosity=2).run(suite)