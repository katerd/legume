# legume. Copyright 2009-2013 Dale Reidy. All rights reserved.
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

class TestAcceptNewConnections(unittest.TestCase):
    def testServerAcceptsConnection(self):
        PORT = getRandomPort()
        self.server = legume.Server()
        self.client = legume.Client()
        
        self.server.listen(('', PORT))
        self.client.connect(('localhost', PORT))
        
        for i in range(100):
            self.update()
            
        self.assertEqual(len(self.server.peers), 1)
        self.assertTrue(self.client.connected)
        
    def testServerDoesNotAcceptNewConnections(self):
        PORT = getRandomPort()
        self.server = legume.Server()
        self.client = legume.Client()
        
        self.server.listen(('', PORT))
        self.server.accept_new_connections = False
        self.client.connect(('localhost', PORT))
        
        for i in range(100):
            self.update()
            
        self.assertEqual(len(self.server.peers), 0)
        self.assertFalse(self.client.connected)
        
    def update(self):
        self.server.update()
        self.client.update()

if __name__ == '__main__':
    from greenbar import GreenBarRunner
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    GreenBarRunner(verbosity=2).run(suite)
