# -*- coding: utf-8 -*-

# legume. Copyright 2009-2013 Dale Reidy. All rights reserved.
# See LICENSE for details.

__docformat__ = 'restructuredtext'

class Metrics(object):

    @property
    def latency(self):
        '''Round-trip latency in ms'''
        return 0

    @property
    def out_buffer_bytes(self):
        '''Count of bytes waiting to be transmitted on the wire.'''
        return 0

    @property
    def pending_acks(self):
        '''Packets that have not yet been acknowledged.'''
        return 0

    @property
    def in_bytes(self):
        '''Count of bytes received (header + data).'''
        return 0

    @property
    def out_bytes(self):
        '''Count of bytes recieved (header + data).'''
        return 0

    @property
    def out_messages(self):
        '''Count of messages sent. Includes connection management messages -
        see legume.messages.messages list.'''
        return 0

    @property
    def in_messages(self):
        '''Count of messages received. Includes connection management messages -
        see legume.messages.messages list.'''

    @property
    def in_packets(self):
        '''Count of packets received.'''
        return 0

    @property
    def out_packets(self):
        '''Count of packets sent.'''
        return 0

    @property
    def keepalive_count(self):
        '''Count of keep-alive Ping or Pong messages sent/received.'''
        return 0

    @property
    def reorder_queue(self):
        '''Number of out-of-order messages received that are waiting to be
        inserted into the message stream.'''
        return 0
