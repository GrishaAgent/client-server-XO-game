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


def flag_val_to_index(flag_val):
    if flag_val:
        return 1
    else:
        return 2


class XOGameServer:
    def __init__(self):
        # initial socket settings
        self.HOST = '127.0.0.1'
        self.PORT = 65432
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # clients dict for server
        self.clients = None

        self.game_field = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
            "0"
        ]

        self.current_turn_info = {
            "pl_type": 0,  # who is on turn - type 1 or type 2
            "x": 0,
            "y": 0
        }

        # events and flags
        self.first_pl_matched = Event()
        self.first_pl_on_turn = Event()
        self.first_pl_on_turn.set()
        self.end_of_game = Event()
        self.game_field_changed = Event()

    def join_clients(self):
        self.clients["1"]["thr"].join()
        self.clients["2"]["thr"].join()
        self.clients["1"]["conn"].close()
        self.clients["2"]["conn"].close()
        self.sock.close()

    def give_pl_type(self):
        # getting known which client is "using"
        if self.first_pl_matched.is_set():
            pregame_data = 2
        else:
            pregame_data = 1
            self.first_pl_matched.set()

        return str(pregame_data)

    def data_synchronise(self, pl_type):
        if self.game_field_changed.is_set():
            with Lock():
                data = code_data(self.game_field)
                self.clients[pl_type]["conn"].send(data)
            print("--- sent data to client: ", pl_type)
            if self.game_field[3] == "0":
                self.game_field_changed.clear()

    def change_game_field(self, pl_type):
        with Lock():
            new_click_coords = self.clients[str(pl_type)]["conn"].recv(1024)
        new_click_coords = decode_data(new_click_coords)
        print("--- received for pl ", pl_type, " : ", new_click_coords)
        y = new_click_coords["y"]
        x = new_click_coords["x"]

        self.game_field[y][x] = pl_type
        with Lock():
            self.game_field_changed.set()

    def handle_client(self):
        pl_type = self.give_pl_type()
        pregame_data = code_data(int(pl_type))
        self.clients[pl_type]["conn"].send(pregame_data)

        while True:
            curr_player_on_turn = flag_val_to_index(self.first_pl_on_turn.is_set())
            if curr_player_on_turn == int(pl_type):
                self.data_synchronise(pl_type)

                self.change_game_field(pl_type)

                if self.calc_win_combination(pl_type) == pl_type:
                    self.end_of_game.set()
                    self.game_field[3] = pl_type
                elif self.calc_win_combination(pl_type) == "3":
                    self.end_of_game.set()
                    self.game_field[3] = "3"
                else:
                    self.switch_clients(curr_player_on_turn)

            if self.end_of_game.is_set():
                print("--- data_synchronise of end_of_game.set")
                self.data_synchronise(pl_type)
                break

            sleep(0.1)

        self.clients[pl_type]["conn"].close()
        print("--- end of game, handle_client executed")
        self.sock.close()

    def switch_clients(self, curr_pl_index):
        if curr_pl_index == 1:
            self.first_pl_on_turn.clear()
        else:
            self.first_pl_on_turn.set()

    def start_socket_connection(self):
        self.sock.bind((self.HOST, self.PORT))
        self.sock.listen(2)

        conn_counter = 1
        while conn_counter <= 2:
            conn, adrr = self.sock.accept()
            conn_thread = Thread(target=self.handle_client)

            if conn_counter == 1:
                self.clients = {str(conn_counter): {"conn": conn, "adrr": adrr, "thr": conn_thread}}
            elif conn_counter == 2:
                second_client = {str(conn_counter): {"conn": conn, "adrr": adrr, "thr": conn_thread}}
                self.clients.update(second_client)

            print("--- ", conn_counter, " connected to:")
            print("  --- conn: ", self.clients[str(conn_counter)]["conn"])
            print("  --- adrr: ", self.clients[str(conn_counter)]["adrr"])

            conn_counter += 1

        print("--- start conn_thr for pl ", str(1))
        self.clients[str(1)]["thr"].start()
        print("--- start conn_thr for pl ", str(2))
        self.clients[str(2)]["thr"].start()

    def calc_win_combination(self, pl_type):
        # copying
        func_game_field = []
        for i in range(3):
            func_game_field.append(self.game_field[i].copy())

        # in row/col test
        for i in range(3):
            if func_game_field[i][0] == func_game_field[i][1] == func_game_field[i][2]:
                if func_game_field[i][0] == pl_type:
                    return pl_type
        for i in range(3):
            if func_game_field[0][i] == func_game_field[1][i] == func_game_field[2][i]:
                if func_game_field[0][i] == pl_type:
                    return pl_type

        # diagonal test
        if func_game_field[0][0] == func_game_field[1][1] == func_game_field[2][2]:
            if func_game_field[0][0] == pl_type:
                return pl_type
        if func_game_field[0][2] == func_game_field[1][1] == func_game_field[2][0]:
            if func_game_field[0][2] == pl_type:
                return pl_type

        # draw
        print(func_game_field)
        is_draw = True
        for i in range(3):
            for j in range(3):
                if func_game_field[i][j] == 0:
                    is_draw = False
        if is_draw:
            return "3"

        # # else
        # return False
