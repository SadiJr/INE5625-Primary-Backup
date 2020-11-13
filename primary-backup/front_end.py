import sys
import os
import socket

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8882


def send_file():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((SERVER_IP, SERVER_PORT))

    filename = 'teste.txt'
    server.send('get_last_id'.encode('utf-8'))

    last_id = int(server.recv(256).decode('utf-8')) + 1
    print('Last Id é ' + str(last_id))

    headers = 'id:' + str(3) + '\nfilename:' + filename + '\n'
    server.send(headers.encode('utf-8'))

    print('Aguardando resposta do server')
    response = server.recv(1024)
    print(response.decode('utf-8'))

    f = open("teste.txt", "rb")

    l = f.read(1024)
    while l:
        server.send(l)
        l = f.read(1024)
        print('a')
    server.close()


if __name__ == '__main__':
    send_file()
