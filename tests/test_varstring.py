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


class ExamplePacket(legume.udp.messages.BaseMessage):
    MessageTypeID = legume.udp.messages.BASE_MESSAGETYPEID_USER+5
    MessageValues = {
        'str':'varstring'}


class TestVarString(unittest.TestCase):
    def setUp(self):
        logger.setLevel(logging.DEBUG)
        self.message_factory = legume.udp.messages.MessageFactory()
        self.message_factory.add(ExamplePacket)

        self.server = legume.udp.Server(self.message_factory)
        self.client = legume.udp.Client(self.message_factory)
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
        time.sleep(0.001)


    def testSendVarStringPacket(self):

        self.test_pass = False

        def Server_OnMessage(sender, message):
            global test_pass
            self.test_pass = (message.str.value == "TEST MESSAGE")

        self.server.OnMessage += Server_OnMessage

        vs = ExamplePacket()
        while not self.client.connected:
            self.update()
        vs.str.value = "TEST MESSAGE"

        self.client.sendMessage(vs)

        for x in xrange(40):
            self.update()

        self.assertTrue(self.test_pass)

if __name__ == '__main__':
    from greenbar import GreenBarRunner
    #logging.basicConfig(level=logging.DEBUG)


    fout = logging.FileHandler('test_events.log', 'w')
    formatter = logging.Formatter('%(asctime)s [%(name)s %(levelname)s] - %(message)s')
    fout.setFormatter(formatter)
    logger.addHandler(fout)
    logger.setLevel(logging.ERROR)

    tests = unittest.TestLoader().loadTestsFromTestCase(TestVarString)
    GreenBarRunner(verbosity=2).run(tests)