# -*- coding: utf-8 -*-
# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

__docformat__ = 'restructuredtext'

from legume.client import Client
from legume.server import Server
from legume.messages import BaseMessage

from legume import serverpeer
from legume import connection
from legume import servicelocator
from legume import exceptions

servicelocator.add('Connection', connection.Connection)
servicelocator.add('Peer', serverpeer.Peer)
