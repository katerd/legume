# legume. Copyright 2009-2013 Dale Reidy. All rights reserved.
# See LICENSE for details.

import sys
import unittest
import legume


class ExamplePacket(legume.messages.BaseMessage):
    MessageTypeID = legume.messages.BASE_MESSAGETYPEID_USER+1
    MessageValues = {
        'player_name' : 'string 32',
        'password' : 'string 8',
        'selected_pmodel' : 'int',
        }

class TestPacketCreation(unittest.TestCase):
    def setUp(self):
        self.ep = ExamplePacket()

    def _breakPasswordValue(self):
        self.ep.password.value = 'toolongxx'

    def testAssignValues(self):
        self.ep.player_name.value = "test"
        self.ep.password.value = "letmein"
        self.ep.selected_pmodel.value = 100

    def testReadValues(self):
        self.ep.player_name.value = "test"
        self.assertEquals(
            self.ep.player_name.value, "test")

    def testStringFieldLimit(self):
        self.assertRaises(
            legume.messages.MessageError,
            self._breakPasswordValue)

if __name__ == '__main__':
    from greenbar import GreenBarRunner
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    GreenBarRunner(verbosity=2).run(suite)
