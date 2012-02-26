# -*- coding: utf-8 -*-

# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

__docformat__ = 'restructuredtext'

import socket
import errno
from legume.exceptions import *

USHRT_MAX = 65535
DEFAULT_TIMEOUT = float(10) # default timeout in seconds
PROTOCOL_VERSION = 4

def isValidPort(port):
    '''
    Returns True if the port parameter is within the
    range 1...65535.
    '''
    return port in range(1, 65535)

class NetworkEndpoint(object):
    DISCONNECTED = 100
    ERRORED = 101
    LISTENING = 102
    CONNECTING = 103
    CONNECTED = 104

    MTU = 1400

    def __init__(self, message_factory):
        self._state = self.DISCONNECTED
        self._socket = None
        self.message_factory = message_factory
        self._timeout = DEFAULT_TIMEOUT

    def __del__(self):
        if self._socket is not None:
            self._socket.close()

    @property
    def timeout(self):
        return self._timeout

    @property
    def socket(self):
        return self._socket

    def setTimeout(self, timeout):
        self._timeout = float(timeout)

    def _create_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)
        return self._socket

    def _shutdown_socket(self):
        self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()

    def _connect_socket(self, addr):
        self._socket.connect(addr)

    def _bind_socket(self, addr):
        self._socket.bind(addr)

    def is_active(self):
        return self._state in [
            self.LISTENING, self.CONNECTING, self.CONNECTED]

    def do_read(self, callback):
        if self._state in [self.LISTENING, self.CONNECTED, self.CONNECTING]:
            if self._socket:
                try:
                    while True:
                        data, addr = self._socket.recvfrom(self.MTU, 0)
                        callback(data, addr)
                except socket.error as e:
                    try:
                        errornum = e.errno
                        if errornum not in [errno.EWOULDBLOCK,errno.ECONNRESET]:
                            raise
                    except:
                        raise
            else:
                raise NetworkEndpointError('Endpoint is not active')

    def get_state(self):
        return self._state
    state = property(get_state)
