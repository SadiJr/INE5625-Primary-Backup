import socket
import sys
import configparser
import os


def save_history(connection):
    try:
        file = open("updates.log", "wb")

        line = connection.recv(1024)
        while line:
            if line.__contains__(b"DONE"):
                break
            file.write(line)
            file.flush()
            line = connection.recv(1024)

        file.close()
        return "200"
    except Exception as e:
        return "500"


def create_or_update(connection, request):
    filename = str(request)

    try:
        file = open(filename, "wb")

        line = connection.recv(1024)
        while line:
            if line.__contains__(b"DONE"):
                break
            file.write(line)
            file.flush()
            line = connection.recv(1024)

        file.close()
        return "200"
    except Exception as e:
        return "500"


def delete(request):
    try:
        filename = request.split(';')[1]
        os.remove(filename)
        return "200"
    except FileNotFoundError as msg:
        return "500"


def backup(connection):
    while True:
        request = connection.recv(1024).decode("UTF-8")

        if request.__contains__("delete"):
            connection.send(delete(request).encode("UTF-8"))
        elif request.__contains__("history"):
            connection.send(save_history(connection).encode("UTF-8"))
        else:
            create_or_update(connection, request)


def init_slave():
    config = configparser.RawConfigParser()
    config.read('slave.conf')

    print(config.keys())

    details_dict = dict(config.items('slave'))

    host = details_dict['ip']
    port = details_dict['port']

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("Iniciando servidor no host {0} e na porta {1}".format(host, port))
    server_address = (host, int(port))

    try:
        sock.bind(server_address)
        print("Servidor de pé")
    except socket.error as msg:
        print("Erro ao fazer o bind do socket. Código do Erro: %s - Mensagem: %s", msg[0], msg[1])
        sys.exit()

    sock.listen(1)

    while True:
        try:
            print("Esperando conexões")
            connection, client = sock.accept()
            print("Conectado com o cliente %s", client)
            backup(connection)
        except Exception as e:
            print("Deu ruim: ", str(e))
            connection.close()

    sock.close()


if __name__ == '__main__':
    init_slave()
