import socket
import sys
import configparser
import os
import traceback


def save_history(connection, filesize):
    print("Iniciando backup dos logs do master....")
    try:
        file = open("updates.log", "wb")
        receive_size = 0

        while receive_size != filesize:
            line = connection.recv(1024)
            file.write(line)
        file.flush()
        file.close()

        print("Backup dos logs do master realizado com sucesso!")
        return "200"
    except Exception as e:
        print("Ocorreu um erro ao fazer o backup dos logs do master. Erro: {0}".format(traceback.print_exc()))
        return "500"


def create_or_update(connection, request):
    filename = str(request).split(";")[0]
    filesize = int(str(request).split(";")[1])

    try:
        file = open(filename, "wb")

        receive_size = 0

        while receive_size != filesize:
            line = connection.recv(1024)
            print("Linha recebida: " + str(line))
            file.write(line)
            receive_size += len(line)
        file.flush()
        file.close()

        print("Arquivo {0} recebido com sucesso!".format(filename))
        return "200"
    except Exception as e:
        print("Ocorreu um erro no upload do arquivo {0}!".format(filename))
        return "500"


def delete(request):
    try:
        filename = request.split(';')[1]
        os.remove(filename)

        print("Arquivo {0} removido com sucesso!".format(filename))
        return "200"
    except FileNotFoundError as msg:
        print("Erro ao remover o arquivo {0}!".format(filename))
        return "500"


def backup(connection):
    while True:
        print("Aguardando novas ordens do master...")

        request = connection.recv(1024).decode()

        if request == b'' or request == '' or not request:
            print("Erro na conexão com o master! Voltando a esperar nova conexão com o master")
            connection.close()
            break

        print("Recebida mensagem do master: {0}".format(request))

        if request.__contains__("delete"):
            print("Iniciando processo de deletar o arquivo {0}".format(request))
            connection.send(delete(request).encode())
        elif request.__contains__("history"):
            print("Iniciando backup do log do master...")
            filesize = request.split(";")[1]
            connection.send(save_history(connection, filesize).encode())
        else:
            filename = request.split(";")[0]
            print("Iniciando recebimento do arquivo {0}".format(filename))
            connection.send(b"OK")
            connection.send(create_or_update(connection, request).encode())

        print("Processo finalizado, aguardando novas instruções...")


def init_slave():
    config = configparser.RawConfigParser()
    config.read('slave.conf')

    print("Lendo configurações do servidor slave")

    details_dict = dict(config.items('slave'))

    host = details_dict['ip']
    port = details_dict['port']

    print("O servidor está configurado para iniciar no host {0} e na porta {1}".format(host, port))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("Iniciando servidor no host {0} e na porta {1}".format(host, port))
    server_address = (host, int(port))

    try:
        sock.bind(server_address)
        print("Servidor iniciado com sucesso!")
    except socket.error as msg:
        print("Erro ao fazer o bind do socket. Código do Erro: {0} - Mensagem: {1}".format(msg[0], msg[1]))
        sys.exit(1)

    sock.listen(1)

    while True:
        try:
            print("Aguardando conexão do master...")
            connection, master = sock.accept()
            print("Conectado com o master {0}".format(master))
            backup(connection)
        except Exception as e:
            print("Um erro inesperado ocorreu, reiniciando servidor")
            traceback.print_exc()
            connection.close()
            sock.close()
            init_slave()


if __name__ == '__main__':
    init_slave()
