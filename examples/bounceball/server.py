#!/usr/bin/env python

import time
import legume
import shared
import random

class ServerBall(shared.Ball):
    BALL_ID = 0
    def __init__(self, env):
        shared.Ball.__init__(self, env)
        self.x = random.randint(0, shared.ZONE_WIDTH)
        self.y = random.randint(0, shared.ZONE_HEIGHT)
        self.vx = random.randint(-200, 200)
        self.vy = random.randint(-200, 200)
        self.ball_id = ServerBall.BALL_ID
        ServerBall.BALL_ID += 1

    def calculate_ahead(self):
        nb = ServerBall(self.env)
        nb.x = (self.x + self.vx)
        nb.y = (self.y + self.vy)
        nb.vx = (self.vx)
        nb.vy = (self.vy)
        nb.frame_number
        return nb

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x > shared.ZONE_WIDTH or self.x < 0: self.vx = -self.vx
        if self.y > shared.ZONE_HEIGHT or self.y < 0: self.vy = -self.vy

    def get_message(self, calculate_ahead=True):
        message = shared.BallUpdate()
        message.ball_id.value = self.ball_id

        if calculate_ahead:
            nb = self.calculate_ahead()
        else:
            nb = self

        message.x.value = nb.x
        message.y.value = nb.y
        message.vx.value = nb.vx
        message.vy.value = nb.vy
        if calculate_ahead:
            message.frame_number.value = nb.frame_number + 1
        else:
            message.frame_number.value = nb.frame_number
        return message


class BallServer(shared.BallEnvironment):
    def __init__(self):
        shared.BallEnvironment.__init__(self)
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

    def spawn_ball(self, position=None):
        if position is None:
            new_ball = ServerBall(self)
            self.insert_ball(new_ball)
        else:
            new_ball = ServerBall(self)
            new_ball.x = position[0]
            new_ball.y = position[1]
            self.insert_ball(new_ball)
        print('Spawning ball with ID %s %s' % (new_ball.ball_id, new_ball.debug()))

    def send_updates(self, server):
        for ball in self._balls.itervalues():
            logging.debug('**** sending update for ball # %s' % ball.ball_id)
            print('Sending update for ball # %s' % ball.ball_id)
            server.send_reliable_message_to_all(ball.get_message())

    def send_initial_state(self, endpoint):
        for ball in self._balls.itervalues():
            endpoint.send_message(ball.get_message(False))




def main():
    server = BallServer()
    server.go()

if __name__ == '__main__':
    import logging
    logging.basicConfig(filename='server.log', level=logging.DEBUG,
        filemode="w",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


    main()
