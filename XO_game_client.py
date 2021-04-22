from tkinter import *
import socket
import json
from threading import Thread, Event, Lock
from time import sleep


# when send data
def code_data(_data):
    new_data = json.dumps(_data)
    new_data = bytearray(new_data, "utf-8")
    return new_data


# when receive data
def decode_data(_data):
    new_data = _data.decode(encoding="utf-8")
    new_data = json.loads(new_data)
    return new_data


def type_to_mark(_type):
    # print("_type: ", _type)
    # print("typeof: ", type(_type))
    if _type == 1:
        return "X"
    elif _type == 2:
        return "O"
    else:
        return "N"


class XOGameClient:
    def __init__(self):
        # initial socket settings
        self.HOST = '127.0.0.1'
        self.PORT = 65432
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Tk settings
        self.window = Tk()
        self.butt_offset = 40
        self.butt_size = 40
        self.butt_field = [
            [Button(), Button(), Button()],
            [Button(), Button(), Button()],
            [Button(), Button(), Button()]
        ]

        # threads
        self.waiting_thr = None

        self.game_field = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]

        self.this_player_type = 0
        self.current_turn_info = {
            "pl_type": 0,  # who is on turn - type 1 or type 2
            "x": 0,
            "y": 0
        }

        # events and flags
        self.pl_suspense = Event()
        self.end_of_game = Event()

    def create_and_start_waiting_thr(self):
        self.waiting_thr = Thread(target=self.waiting_function)
        self.waiting_thr.start()

    def waiting_function(self):
        self.pl_suspense.set()

        while True:
            with Lock():
                received_data = self.sock.recv(1024)
            if received_data:
                received_data = decode_data(received_data)
                self.actualise_game_field(received_data)
                self.pl_suspense.clear()
                break

    def start_socket_connection(self):
        self.sock.connect((self.HOST, self.PORT))
        pregame_data = self.sock.recv(1024)
        pregame_data = decode_data(pregame_data)

        print("--- got pregame data (pl type): ", pregame_data)

        self.current_turn_info["pl_type"] = pregame_data
        self.this_player_type = pregame_data
        self.window.title(self.this_player_type)

        if self.this_player_type == 2:
            self.pl_suspense.set()
            self.create_and_start_waiting_thr()
            while not self.pl_suspense.is_set():
                sleep(0.05)

    def change_player(self, pl_type):
        if self.game_field[self.current_turn_info["y"]][self.current_turn_info["x"]] == pl_type:
            print("THIS PLACE IS ALREADY MARKED, CHOOSE ANOTHER")
            return False
        elif self.game_field[self.current_turn_info["y"]][self.current_turn_info["x"]] != 0 and \
                self.game_field[self.current_turn_info["y"]][self.current_turn_info["x"]] != pl_type:
            print("THIS PLACE IS MARKED BY SECOND PLAYER, CHOOSE ANOTHER")
            return False
        else:
            return True

    def actualise_game_field(self, data):
        print("actualise_game_field 1")
        for i in range(3):
            for j in range(3):
                data[i][j] = int(data[i][j])
        self.game_field = data
        print("actualise_game_field 2")
        for i in range(3):
            for j in range(3):
                if type_to_mark(self.game_field[i][j]) == "N":
                    continue
                else:
                    self.butt_field[i][j]["text"] = type_to_mark(self.game_field[i][j])
                    print("i: ", i)
                    print("j: ", j)
        print("actualise_game_field 3")

        print("data[3]: ", str(data[3]))
        if data[3] != "0":
            self.end_of_game.set()
            print("winner: ", str(data[3]))
            if int(data[3]) == self.this_player_type:
                print("YOU WON, CG MAZAFAKA")
                end_mess = Label(text="YOU WON, CG MAZAFAKA", fg="red").place(x=20, y=20)
            elif int(data[3]) == 3:
                print("DRAW FAKAS")
                end_mess = Label(text="DRAW FAKAS", fg="red").place(x=20, y=20)
            else:
                print("YOU LOST, ¯\\_('',)_/¯")
                end_mess = Label(text="YOU LOST, ¯\\_('',)_/¯", fg="red").place(x=20, y=20)

    def change_game_field(self):
        print("--- change_game_field")

        if self.current_turn_info["pl_type"] == 1:
            self.butt_field[self.current_turn_info["y"]][self.current_turn_info["x"]]["text"] = "X"
        if self.current_turn_info["pl_type"] == 2:
            self.butt_field[self.current_turn_info["y"]][self.current_turn_info["x"]]["text"] = "O"

        print("  --- game_field changed")

        self.game_field[self.current_turn_info["y"]][self.current_turn_info["x"]] = self.current_turn_info["pl_type"]

    def get_click_coords(self, event):
        if self.pl_suspense.is_set():
            print("DUMMY, YOU ARE NOT ON TURN")
            return

        print("--- get_click_coords")
        # getting coords where pl clicks
        # getting X and Y position
        butt_name = str(event.widget)
        butt_number = butt_name[-1]

        # checking for the first button
        if butt_number == "n":
            butt_number = 1
        else:
            butt_number = int(butt_number)

        y = int((butt_number - 1) / 3)
        x = (butt_number - 1) % 3
        butt_coords = {"x": x, "y": y}

        self.current_turn_info.update(butt_coords)

        print("  --- coords of curr click: ", self.current_turn_info)

        self.processing_pl_turn(butt_coords)

    def processing_pl_turn(self, new_coords):
        print("--- processing_pl_turn")
        # data about current turn
        print("--- data about current turn: ", self.current_turn_info)

        print("--- calc if we can change pl")
        change_pl = self.change_player(self.this_player_type)

        print("  --- change pl? : ", change_pl)

        if change_pl:
            self.change_game_field()

            data = code_data(new_coords)
            self.sock.send(data)

            self.create_and_start_waiting_thr()
            while not self.pl_suspense.is_set():
                sleep(1)

            print("")
            if self.end_of_game.is_set():
                self.window.destroy()
                self.__del__()

    def placing_buttons(self):
        print("--- placing of buttons")
        for i in range(3):
            for j in range(3):
                butt = self.butt_field[i][j]
                butt.place(width=self.butt_size, height=self.butt_size,
                           x=self.butt_offset * j, y=self.butt_offset * i)

    def handle_button_click(self):
        print("--- binding buttons")
        for i in range(3):
            for j in range(3):
                butt = self.butt_field[i][j]
                butt.bind("<Button-1>", self.get_click_coords)

    def game_cycle(self):
        self.placing_buttons()
        self.start_socket_connection()
        self.handle_button_click()

    def __del__(self):
        self.sock.close()

# The only thread there is waiting thread.
# In game cycle I just need to use several functions in right way (it means
# also "function for starting waiting thread").
# Then code will be easier and there will not be problems with placing/binding buttons ( this
# two stuffs have to be in main thread of the program).
