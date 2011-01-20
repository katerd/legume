# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

__docformat__ = 'restructuredtext'

import udp
import udp.serverpeer
import udp.connection
import servicelocator
import exceptions

servicelocator.add('Connection', udp.connection.Connection)
servicelocator.add('Peer', udp.serverpeer.Peer)
