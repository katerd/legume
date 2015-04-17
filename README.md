#legume

Designed primarily for use in multiplayer games, legume provides non-reliable, reliable and in-order transmission of messages via UDP. The focus behind the features and design of legume:

  * Cater for the networking requirements of a multiplayer game with as little boiler-plate code as possible.
  * Peaceful co-existence with widely-used game development frameworks and libraries such as pygame and pyglet.
  * Don't rely on third-party libraries or platform specific functionality.

An example client with an event handler:
```python
import legume
from time import sleep

def on_connected(sender, event_args):
   print 'Connected to server'

client = legume.Client()
client.OnConnectRequestAccepted += on_connected
client.connect(('host.example.com', 4000))

while True:
    client.update()
    sleep(0.001)
```

To define a new message, specify a MessageTypeID to uniquely identity that particular message structure, and a MessageValues dictionary (key=value, value=type):
```python
class PlayerJoin(legume.messages.BaseMessage):
    MessageTypeID = 100
    MessageValues = {
        'player_name'     : 'string 32', # 32 char ansi string
        'player_model_id' : 'int',
        'start_x'         : 'float',
        'start_y'         : 'float'
    }

class ChatMessage(legume.messages.BaseMessage):
    MessageTypeID = 2
    MessageValues = {
        'num'       : 'int',
        'message'    : 'varstring'
    }
```

Sending a message:
```python
msg = ChatMessage()
msg.num.value = 1
msg.message.value = "Hello from the Internet!"

server.send_message_to_all(msg, reliable=True)
```
