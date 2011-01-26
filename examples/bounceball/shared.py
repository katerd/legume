import time
import legume
import random

PORT = 27806

ZONE_SCREEN_WIDTH = 400
ZONE_SCREEN_HEIGHT = 400

ZONE_WIDTH = 40000
ZONE_HEIGHT = 40000

UPDATE_RATE = 1.0
UPDATES_PER_SECOND = 1.0 / UPDATE_RATE
print 'Network update rate:', UPDATES_PER_SECOND

PHYSICS_RATE = 0.01

PHYSICS_FRAMES_PER_SECOND = 1.0 / PHYSICS_RATE
print 'Physics update rate:', PHYSICS_FRAMES_PER_SECOND

class BallUpdate(legume.messages.BaseMessage):
    MessageTypeID = legume.messages.BASE_MESSAGETYPEID_USER+1
    MessageValues = {
        'ball_id' : 'int',
        'frame_number' : 'int',
        'x' : 'int',
        'y' : 'int',
        'vx' : 'int',
        'vy' : 'int'}

class CreateBallCommand(legume.messages.BaseMessage):
    MessageTypeID = legume.messages.BASE_MESSAGETYPEID_USER+2
    MessageValues = {
        'x' : 'int',
        'y' : 'int'}

legume.messages.message_factory.add(BallUpdate)
legume.messages.message_factory.add(CreateBallCommand)

class BallEnvironment(object):
    def __init__(self):
        self._balls = {}
        self._frame_timer = time.time()
        self._frame_accumulator = 0
        self._frame_number = 0

    def _get_frame_number(self):
        return self._frame_number
    frame_number = property(_get_frame_number)

    def get_ball_positions(self):
        return [(ball.x, ball.y) for ball in self._balls.itervalues()]

    def insert_ball(self, ball):
        self._balls[ball.ball_id] = ball

    def _update_balls(self):
        newtime = time.time()
        deltatime = newtime - self._frame_timer
        self._frame_timer = newtime
        self._frame_accumulator += deltatime

        while self._frame_accumulator >= PHYSICS_RATE:
            self._frame_accumulator -= PHYSICS_RATE
            for ball in self._balls.itervalues():
                ball.update()
            self._frame_number += 1

class Ball(object):
    def __init__(self, env):
        self.env = env
        self.ball_id = 0
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.last_resync = 0
        self.last_resync_frames = 0
        self.force_resync = True

    def _get_frame_number(self):
        return self.env.frame_number
    frame_number = property(_get_frame_number)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x > ZONE_WIDTH or self.x < 0: self.vx = -self.vx
        if self.y > ZONE_HEIGHT or self.y < 0: self.vy = -self.vy

    def load_from_message(self, message):

        if ((message.frame_number.value >= self.frame_number) or
            (time.time() - self.last_resync > 2.0)) or self.force_resync:
            self.force_resync = False
            self.ball_id = message.ball_id.value
            self.x = message.x.value
            self.y = message.y.value
            self.vx = message.vx.value
            self.vy = message.vy.value
            self.last_resync = time.time()
            self.last_resync_frames = self.frame_number

    def debug(self):
        return '%s, %s, %s, %s, %s' % (
            self.x, self.y, self.vx, self.vy, self.frame_number)


