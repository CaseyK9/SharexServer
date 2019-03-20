from libs import Player, Room, Matcher
import database, socket, json

#HOSTNAME, PORT = "0.0.0.0", 4466
HOSTNAME, PORT = "localhost", 80

if __name__ == '__main__':
    """ ################ Setting up the socket ################ """
    SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER.bind((HOSTNAME, PORT))
    SERVER.listen(5)

    """ ################ firing up the server ################ """
    print("Server started on main thread")
    while True:
        client_socket, client_address = SERVER.accept()
        print("New IP: %s" % client_address[0])
        Player(client_socket).start()
