import socket

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8882


def connect():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((SERVER_IP, SERVER_PORT))

    server.send('get_last_id'.encode('utf-8'))

    return server


def send_file():

    server = connect()
    last_id = int(server.recv(256).decode('utf-8')) + 1
    print('Last Id é ' + str(last_id))

    filename = 'teste.txt'
    headers = 'id:' + str(last_id) + '\nfilename:' + filename + '\n'
    server.send(headers.encode('utf-8'))

    print('Aguardando resposta do server')
    f = open("teste.txt", "rb")

    line = f.read(1024)
    while line:
        server.send(line)
        line = f.read(1024)
    server.close()


if __name__ == '__main__':
    send_file()
