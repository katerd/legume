# legume. Copyright 2009-2013 Dale Reidy. All rights reserved.
# See LICENSE for details.

import sys
sys.path.append('..')
import legume.timing as time
import unittest
import legume
from greenbar import GreenBarRunner


def getRandomPort():
    import random
    return random.randint(16000, 50000)


class TestKeepAlive(unittest.TestCase):
    def setUp(self):
        self.port = getRandomPort()
        self.server = legume.Server()
        self.client = legume.Client()

    def initEndpoints(self):
        self.server.listen(('', self.port))
        self.client.connect(('localhost', self.port))

    def performUpdateLoop(self):
        for i in range(60):
            self.server.update()
            self.client.update()
            time.sleep(0.01)

    def testKeepAliveClientWillDisconnect(self):
        '''
        Client will connect to Server but connection will timeout
        and Client will go into an errored state.
        '''
        self.initEndpoints()

        # Mismatched timeout causes client to bail on the connection early.
        self.server.setTimeout(1.0)
        self.client.setTimeout(0.25)

        self.performUpdateLoop()
        self.assertTrue(self.client.errored)

    def testKeepAliveClientWillStayConnected(self):
        '''
        Client will stay connected to the server
        '''
        self.initEndpoints()

        self.server.setTimeout(0.25)
        self.client.setTimeout(0.25)

        self.performUpdateLoop()
        self.assertTrue(self.client.connected)



if __name__ == '__main__':
    mytests = unittest.TestLoader().loadTestsFromTestCase(TestKeepAlive)
    GreenBarRunner(verbosity=2).run(mytests)