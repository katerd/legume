# legume. Copyright 2009 Dale Reidy. All rights reserved. See LICENSE for details.

import legume.timing as time
import random
import unittest
import legume
from greenbar import GreenBarRunner

FIRED = False

class Handler(object):
    def __init__(self):
        pass

    def _handler(self, sender, event):
        global FIRED
        FIRED = True

    def __del__(self):
        pass

HANDLER = Handler()

class NEventTests(unittest.TestCase):
    def setUp(self):
        self.ne = legume.nevent.Event()
        self.event_raised = False
        #self.handler = Handler()
        FIRED = False

    def testAddHandler(self):
        self.ne += HANDLER._handler
        self.assertTrue(self.ne.is_handled_by(HANDLER._handler))

    def testAddHandlerTwiceRaisesError(self):
        def addhandler():
            print self.ne._handlers
            self.ne += HANDLER._handler

        addhandler()
        self.assertRaises(legume.nevent.NEventError, addhandler)

    def testRemoveHandler(self):
        self.ne += HANDLER._handler
        self.ne -= HANDLER._handler

        self.assertFalse(self.ne.is_handled_by(HANDLER._handler))

    def testRaisesEvent(self):
        global FIRED
        self.ne += HANDLER._handler
        self.ne(self, None)
        self.assertTrue(FIRED)


if __name__ == '__main__':
    mytests = unittest.TestLoader().loadTestsFromTestCase(NEventTests)
    GreenBarRunner(verbosity=2).run(mytests)