import time
import legume
import random

PORT = 27806

ZONE_SCREEN_WIDTH = 400
ZONE_SCREEN_HEIGHT = 400

ZONE_WIDTH = 40000
ZONE_HEIGHT = 40000

UPDATE_RATE = 0.5
UPDATES_PER_SECOND = 1.0 / UPDATE_RATE
print 'Network update rate:', UPDATES_PER_SECOND

PHYSICS_RATE = 0.01

PHYSICS_FRAMES_PER_SECOND = 1.0 / PHYSICS_RATE
print 'Physics update rate:', PHYSICS_FRAMES_PER_SECOND

class BallUpdate(legume.udp.messages.BaseMessage):
    MessageTypeID = legume.udp.messages.BASE_MESSAGETYPEID_USER+1
    MessageValues = {
        'ball_id' : 'int',
        'frame_number' : 'int',
        'x' : 'int',
        'y' : 'int',
        'vx' : 'int',
        'vy' : 'int'}

class CreateBallCommand(legume.udp.messages.BaseMessage):
    MessageTypeID = legume.udp.messages.BASE_MESSAGETYPEID_USER+2
    MessageValues = {
        'x' : 'int',
        'y' : 'int'}

legume.udp.messages.message_factory.add(BallUpdate)
legume.udp.messages.message_factory.add(CreateBallCommand)

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
        # TODO: change this into a list comprehension
        result = []
        for ball in self._balls.itervalues():
            result.append((ball.x, ball.y))
        return result

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


class ClientBallEnvironment(BallEnvironment):
    def force_resync(self):
        for ball in self._balls.itervalues():
            ball.force_resync = True

    def load_ball_from_message(self, message):
        print('Got status for ball %s' % message.ball_id.value)
        if message.ball_id.value not in self._balls:
            print 'Creating new ball'
            new_ball = Ball(self)
            new_ball.load_from_message(message)
            self.insert_ball(new_ball)
        else:
            self._balls[message.ball_id.value].load_from_message(message)

    def spawn_ball(self, endpoint, position):
        message = CreateBallCommand()
        message.x.value = position[0]
        message.y.value = position[1]
        endpoint.send_message(message)


class ServerBallEnvironment(BallEnvironment):
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
            print('Sending update for ball # %s' % ball.ball_id)
            server.send_messageToAll(ball.get_message())

    def send_initial_state(self, endpoint):
        for ball in self._balls.itervalues():
            endpoint.send_message(ball.get_message(False))


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


class ServerBall(Ball):
    BALL_ID = 0
    def __init__(self, env):
        Ball.__init__(self, env)
        self.x = random.randint(0, ZONE_WIDTH)
        self.y = random.randint(0, ZONE_HEIGHT)
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
        if self.x > ZONE_WIDTH or self.x < 0: self.vx = -self.vx
        if self.y > ZONE_HEIGHT or self.y < 0: self.vy = -self.vy

    def get_message(self, calculate_ahead=True):
        message = BallUpdate()
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
