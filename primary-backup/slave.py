import socket
import sys

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8882


def init_slave():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((SERVER_IP, SERVER_PORT))

    server.send('get_last_id'.encode('utf-8'))
    last_id = int(server.recv(256).decode('utf-8')) + 1
    print('Last Id é ' + str(last_id))


if __name__ == '__main__':
    init_slave()
