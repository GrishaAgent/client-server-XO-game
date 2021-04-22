## client-server-XO-game
Client-server XO game written on python :money_mouth_face:

### Used python modules
```
from tkinter import *
import socket
import json
from threading import Thread, Event, Lock
from time import sleep
```
### XO_game_client.py
Have two fileds:
- `game_field` - contains 3x3 python list with data about game field ("X" is there noted as "1", "O" is noted as "2"
- `butt_field` - caontains 3x3 python list of tkinter Button class object - this field is used for graphics
