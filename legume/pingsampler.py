# -*- coding: utf-8 -*-
# legume. Copyright 2009 Dale Reidy. All rights reserved.
# See LICENSE for details.

__docformat__ = 'restructuredtext'

class PingSampler(object):
    def __init__(self, num_samples=4):
        self._num_samples = num_samples
        self._samples = []

    def has_estimate(self):
        return len(self._samples) > 0

    def add_sample(self, sample):
        if sample >= 0:
            self._samples = (self._samples + [sample])[-self._num_samples:]

    def get_ping(self):
        if len(self._samples) == 0:
            return 0
        else:
            return sum(self._samples) / float(len(self._samples))

