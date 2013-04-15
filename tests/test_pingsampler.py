# legume. Copyright 2009-2013 Dale Reidy. All rights reserved.
# See LICENSE for details.

import legume.timing as time
import random
import unittest
import legume
from greenbar import GreenBarRunner

class PingSamplerTests(unittest.TestCase):
    def setUp(self):
        self.ps = legume.pingsampler.PingSampler(5)

    def testLessThanMaximumSamples(self):
        self.ps.add_sample(4)
        self.ps.add_sample(4)
        self.ps.add_sample(4)
        self.assertEquals(self.ps.get_ping(), 4)

    def testMaximumSamples(self):
        self.ps.add_sample(10000)
        self.ps.add_sample(4)
        self.ps.add_sample(4)
        self.ps.add_sample(4)
        self.ps.add_sample(4)
        self.ps.add_sample(4)
        self.assertEquals(self.ps.get_ping(), 4)

    def testIgnoresNegativeSamples(self):
        self.ps.add_sample(4)
        self.ps.add_sample(-4)
        self.ps.add_sample(4)
        self.ps.add_sample(-4)
        self.assertEquals(self.ps.get_ping(), 4)

    def testDoesntBreakWithNoSamples(self):
        self.ps.get_ping()


if __name__ == '__main__':
    mytests = unittest.TestLoader().loadTestsFromTestCase(PingSamplerTests)
    GreenBarRunner(verbosity=2).run(mytests)