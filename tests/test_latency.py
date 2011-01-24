# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

import legume.timing as time
import random
import unittest
import legume
from greenbar import GreenBarRunner

HOST = 'localhost'

def getRandomPort():
    return random.randint(16000, 50000)

class TestLatency(unittest.TestCase):
    def setUp(self):
        self.mf = legume.messages.MessageFactory()
        self.server = legume.Server(self.mf)
        self.client = legume.Client(self.mf)
        port = getRandomPort()
        self.server.listen((HOST, port))
        self.client.connect((HOST, port))

    def testLatency(self):
        iterations = 100
        for x in xrange(iterations):
            self.server.update()
            self.client.update()
        print self.client.latency

if __name__ == '__main__':
    tests = unittest.TestLoader().loadTestsFromTestCase(TestLatency)
    GreenBarRunner(verbosity=2).run(tests)
