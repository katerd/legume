# legume. Copyright 2009 Dale Reidy. All rights reserved.
# See LICENSE for details.

__docformat__ = 'restructuredtext'

import udp
import servicelocator
from udp.connection import Connection

servicelocator.add('Connection', Connection)