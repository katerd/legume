#!/usr/bin/env python

import time
import legume
import shared

class BallServer(shared.ServerBallEnvironment):
    def __init__(self):
        shared.ServerBallEnvironment.__init__(self)
        self._server = legume.Server()
        self._server.OnConnectRequest += self.join_request_handler
        self._server.OnMessage += self.message_handler
        self._update_timer = time.time()
        self.checkup_timer = time.time()
        self.checkup_framecount = 0

    def message_handler(self, sender, message):
        if message.MessageTypeID == shared.CreateBallCommand.MessageTypeID:
            self.spawn_ball((message.x.value, message.y.value))

    def join_request_handler(self, sender, args):
        self.send_initial_state(sender)

    def _send_update(self):
        self.send_updates(self._server)

    def go(self):
        self._server.listen(('', shared.PORT))
        print('Listening on port %d' % shared.PORT)

        for x in xrange(1):
            self.spawn_ball()

        while True:
            # Physics stuff
            self._update_balls()

            if time.time()-self.checkup_timer >= 3.0:
                print 'Frames:', self.frame_number - self.checkup_framecount,
                print 'Time:', time.time() - self.checkup_timer
                self.checkup_timer = time.time()
                self.checkup_framecount = self.frame_number

            # Network stuff
            if time.time() > self._update_timer + shared.UPDATE_RATE:
                self._send_update()
                self._update_timer = time.time()
            self._server.update()
            time.sleep(0.0001)



def main():
    server = BallServer()
    server.go()

if __name__ == '__main__':
    main()