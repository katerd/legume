# -*- coding: utf-8 -*-
# legume. Copyright 2009-2010 Dale Reidy. All rights reserved.
# See LICENSE for details.

import struct
from legume.exceptions import BufferError

class ByteBuffer(object):
    '''
    Provides a simplified method of reading struct packed data from
    a string buffer.

    read_bytes and read_struct remove the read data from the string buffer.
    '''
    def __init__(self, bytes):
        self._bytes = bytes

    def read_bytes(self, bytes_to_read):
        if bytes_to_read > len(self._bytes):
            raise BufferError, (
                'Cannot read %d bytes, buffer too small (%d bytes)' \
                % (bytes_to_read, len(self._bytes)))
        result = self._bytes[:bytes_to_read]
        self._bytes = self._bytes[bytes_to_read:]
        return result

    def peek_bytes(self, bytes_to_peek):
        if bytes_to_peek > len(self._bytes):
            raise BufferError, (
                'Cannot peek %d bytes, buffer too small (%d bytes)' \
                % (bytes_to_peek, len(self._bytes)))
        return self._bytes[:bytes_to_peek]

    def push_bytes(self, bytes):
        self._bytes += bytes

    def read_struct(self, struct_format):
        struct_size = struct.calcsize('!'+struct_format)
        try:
            struct_bytes = self.read_bytes(struct_size)
            bytes = struct.unpack('!'+struct_format, struct_bytes)
        except struct.error, e:
            raise BufferError, 'Unable to unpack data'
        except BufferError, e:
            raise BufferError(
                'Could not unpack using format %s' % struct_format, e)
        return bytes

    def peek_struct(self, struct_format):
        struct_size = struct.calcsize('!'+struct_format)
        try:
            struct_bytes = self.peek_bytes(struct_size)
            bytes = struct.unpack('!'+struct_format, struct_bytes)
        except struct.error, e:
            raise BufferError, 'Unable to unpack data'
        except BufferError, e:
            raise BufferError(
                'Could not unpack using format %s' % struct_format, e)
        return bytes

    def is_empty(self):
        return len(self._bytes) == 0

    @property
    def length(self):
        return len(self._bytes)