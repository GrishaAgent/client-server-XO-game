from XO_game_server import *

server = XOGameServer()
server.start_socket_connection()

# while True:
#     try:
#         sleep(1)
#     except KeyboardInterrupt:
#         server.end_of_game.set()
#         server.join_clients()
#         sleep(3)
#         exit()
