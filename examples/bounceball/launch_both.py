#!/usr/bin/env python

from subprocess import Popen

client = Popen(["python", "client.py"])
server = Popen(["python", "server.py"])

client.wait()
server.kill()