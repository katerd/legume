#!/usr/bin/env python

import threading
import time
import legume
import shared
import pyglet
import sys

LOCALHOST = 'localhost'
REMOTEHOST = 'aura.psyogenix.co.uk'

VSYNC = True

class BallClient(shared.BallEnvironment):
    def __init__(self):
        self.running = True
        shared.BallEnvironment.__init__(self)
        self._client = legume.Client()
        self._client.OnMessage += self.message_handler
        self.lastdelta = time.time()
        self.lock = threading.Lock()
        self.ball_positions = None

    def message_handler(self, sender, args):
        if legume.messages.message_factory.is_a(args, 'BallUpdate'):
            self.load_ball_from_message(args)
        else:
            print 'Message: %s' % args

    def connect(self, host='localhost'):
        self._client.connect((host, shared.PORT))

    def go(self):
        while self.running:
            try:
                self._update_balls()
                self.lock.acquire()
                self._client.update()
                self.lastdelta = time.time()
                self.ball_positions = self.get_ball_positions()
            except:
                self.running = False
                raise
            finally:
                pass
                self.lock.release()
            time.sleep(0.0001)
        print('Exited go')

    def force_resync(self):
        for ball in self._balls.itervalues():
            ball.force_resync = True

    def load_ball_from_message(self, message):
        print('Got status for ball %s' % message.ball_id.value)
        if message.ball_id.value not in self._balls:
            print 'Creating new ball'
            new_ball = shared.Ball(self)
            new_ball.load_from_message(message)
            self.insert_ball(new_ball)
        else:
            self._balls[message.ball_id.value].load_from_message(message)

    def spawn_ball(self, endpoint, position):
        message = shared.CreateBallCommand()
        message.x.value = position[0]
        message.y.value = position[1]
        endpoint.send_message(message)

    def showlatency(self, dt):
        print('latency: %3.3f    fps:%3.3f' % (
            self._client.latency, pyglet.clock.get_fps()))


def main():
    if "--remote" in sys.argv:
        host = REMOTEHOST
    else:
        host = LOCALHOST
    print('Using host: %s' % host)

    client = BallClient()
    client.connect(host)

    ball_image = pyglet.image.load('ball.png')
    ball_sprite = pyglet.sprite.Sprite(ball_image)

    w = pyglet.window.Window(vsync=VSYNC)

    x_ratio = float(shared.ZONE_WIDTH) / shared.ZONE_SCREEN_WIDTH
    y_ratio = float(shared.ZONE_HEIGHT) / shared.ZONE_SCREEN_HEIGHT

    @w.event
    def on_key_press(s, m):
        if s == 114: # "r"
            client.force_resync()

    @w.event
    def on_mouse_press(x, y, b, m):
        if b == 4: # right click
            print 'Clicked'
            client.lock.acquire()
            client.spawn_ball(client._client, (x*x_ratio, y*y_ratio))
            client.lock.release()

    @w.event
    def on_show():
        client.force_resync()

    @w.event
    def on_close():
        client.running = False

    @w.event
    def on_draw():
        w.clear()

        if client.ball_positions is not None:
            for x, y in client.ball_positions:
                x /= x_ratio
                y /= y_ratio
                ball_sprite.set_position(x, y)
                ball_sprite.draw()

    #pyglet.clock.schedule_interval(client.showlatency, 0.75)

    # keep pyglet draw running regularly.
    def b(dt): pass
    pyglet.clock.schedule(b)

    net_thread = threading.Thread(target=client.go)
    net_thread.start()

    pyglet.app.run()
    client.running = False

if __name__ == '__main__':
    import logging
    logging.basicConfig(filename='client.log', level=logging.DEBUG)
    main()
