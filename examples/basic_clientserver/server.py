#!/usr/bin/env python

import legume
import time

PORT = 29050

def main():
    s = legume.udp.Server()
    s.listen(('', PORT))

    t = time.time()

    while True:
        s.update()

        if time.time() > t + 1.0:
            t = time.time()
            for peer in s.peers:
                print peer.getAddress(), peer.latency

        time.sleep(0.0001)

if __name__ == '__main__':
    main()
