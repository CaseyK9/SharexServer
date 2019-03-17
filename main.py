from libs import Player, Room, Matcher
import database, socket, json

HOSTNAME, PORT = "0.0.0.0", 4466
#HOSTNAME, PORT = "localhost", 80

if __name__ == '__main__':
    """ ################ Setting up the socket ################ """
    SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER.bind((HOSTNAME, PORT))
    SERVER.listen(5)


    """ ################ Setting up the rooms ################ """
    matcher = Matcher()
    for server_id in range(len(database.rooms_name)):
        room = Room(database.rooms_name[server_id], 5, database.rooms_min_bet[server_id], database.rooms_max_bet[server_id])
        matcher.add_room(room)
        room.start()


    """ ################ firing up the server ################ """
    print("Server started on main thread")
    while True:
        client_socket, client_address = SERVER.accept()
        print("New IP: %s" % client_address[0])
        Player(client_socket, matcher).start()
