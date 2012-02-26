#!/usr/bin/env python

import legume
import time
import sys
import logging

LOCALHOST = 'localhost'
REMOTEHOST = 'aura.psyogenix.co.uk'
PORT = 29050

logging.basicConfig(level=logging.INFO)

def main():
    if "--remote" in sys.argv:
        host = REMOTEHOST
    else:
        host = LOCALHOST

    print('Using host: %s' % host)

    t = time.time()
    c = legume.Client()
    c.connect((host, PORT))

    while c.state != c.ERRORED:
        c.update()
        if (c.state == c.CONNECTED):
            if time.time() > t + 1.0:
                t = time.time()
                print c.latency
        time.sleep(0.0001)
    if (c.state == c.ERRORED):
        print 'Connection Error'

if __name__ == '__main__':
    main()
