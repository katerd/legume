# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

import legume.timing as time
time.test_mode(True)

import sys

import unittest
from greenbar import GreenBarRunner
import test_udp
import test_keepalive
import test_events
import test_nevent
import test_newmsg
import test_pingsampler
import test_latency
import test_varstring
import test_reliablemsg
import test_metrics
import test_api

import logging

if __name__ == '__main__':

    logger = logging.getLogger()
    fout = logging.FileHandler('test_events.log', 'w')
    formatter = logging.Formatter('%(asctime)s [%(name)s %(levelname)s] - %(message)s')
    fout.setFormatter(formatter)
    logger.addHandler(fout)
    logger.setLevel(logging.ERROR)

    suite_udp = unittest.TestLoader().loadTestsFromModule(test_udp)
    suite_keepalive = unittest.TestLoader().loadTestsFromModule(test_keepalive)
    suite_events = unittest.TestLoader().loadTestsFromModule(test_events)
    suite_nevent = unittest.TestLoader().loadTestsFromModule(test_nevent)
    suite_pingsampler = unittest.TestLoader().loadTestsFromModule(test_pingsampler)
    suite_newmsg = unittest.TestLoader().loadTestsFromModule(test_newmsg)
    suite_latency = unittest.TestLoader().loadTestsFromModule(test_latency)
    suite_varstring = unittest.TestLoader().loadTestsFromModule(test_varstring)
    suite_reliablemsg = unittest.TestLoader().loadTestsFromModule(test_reliablemsg)
    suite_metrics = unittest.TestLoader().loadTestsFromModule(test_metrics)
    suite_api = unittest.TestLoader().loadTestsFromModule(test_api)

    all_suites = unittest.TestSuite()
    all_suites.addTests([
        suite_udp, suite_keepalive, suite_events,
        suite_nevent, suite_pingsampler, suite_newmsg,
        suite_latency, suite_varstring, suite_reliablemsg,
        suite_metrics, suite_api
    ])

    if len(sys.argv) > 1:
        repetitions = int(sys.argv[1])
    else:
        repetitions = 1

    for x in range(repetitions):
        GreenBarRunner(verbosity=2).run(all_suites)