import socket
import sys
import os
from pathlib import Path
# TODO Adicionar configurações de servidor e porta em um
# arquivo de configuração
HOST = "127.0.0.1"
PORT = 8882


def verify_if_log_exists():
    file = Path("updates.log")
    if file.is_file():
        return True
    return False


def verify_if_request_exists(request_id, con):
    if verify_if_log_exists:
        split_char = ";"
        with open("updates.log", "r") as f:
            lines = f.read().split("\n")

        for line in lines:
            if request_id in line.split(split_char)[0]:
                print("Request já realizado, com a resposta sendo " + line)
                temp = line.split(split_char)
                answer = split_char.join(temp[1:])
                con.send(answer)
                return True
    return False


def write_log(client_id, anwser):
    # Formato do arquivo de log:
    # "Id do request do cliente","resposta do servidor"
    f = open("updates.log", "a+")
    f.write(client_id + ";" + anwser + "\n")


def send_data_to_slaves(data):
    print("Falta fazer")
    return "Resposta temporária"


def receive_file(con, filename, identifier):
    print("Filename: " + filename + " - id: " + identifier)
    file = open(filename, "wb")

    while True:
        data = con.recv(1024)
        while data:
            file.write(data)
            data = con.recv(1024)
        break
    answer = send_data_to_slaves(file)
    write_log(identifier, answer)
    file.close()


def get_last_id():
    if verify_if_log_exists():
        print("Arquivo existe!")
        with open("updates.log", "r") as f:
            lines = f.read().splitlines()
            last_line = lines[-1]
            identifier = last_line.split(";")[0]
            return int(identifier)
    return 0


def conn(con, client):
    while True:
        print("Iniciando conexão com o cliente ", client)

        message = con.recv(256).decode("utf-8")

        print("Mensagem recebida do cliente: " + message)
        if not message:
            return
        if message == "get_last_id":
            con.send(str(get_last_id()).encode("utf-8"))
        elif message.__contains__("id"):

            for line in message.split("\n"):
                if line.startswith("id:"):
                    identifier = line.split(":")[1]
                elif line.startswith("filename:"):
                    filename = line.split(":")[1]

            if verify_if_request_exists(identifier, con):
                con.send("Resposta já arquivada".encode("utf-8"))
                con.close()
            else:
                con.send("Manda o arquivo, puto".encode("utf-8"))
                receive_file(con, filename, identifier)
        else:
            con.send("Ocorreu um erro. Vai tomar no cu")
            con.close()
            break


def init_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (HOST, PORT)

    try:
        sock.bind(server_address)
    except socket.error as msg:
        print("Erro ao fazer o bind do socket. Código do Erro: %s - Mensagem: %s", msg[0], msg[1])
        sys.exit()

    print("Iniciando servidor com o IP %s na porta %s" % sock.getsockname())
    sock.listen(1)
    while True:
        try:
            print("Esperando conexões")
            connection, client = sock.accept()
            conn(connection, client)
        except Exception as e:
            print("Deu ruim: ", str(e))
            connection.close()

    sock.close()


if __name__ == "__main__":
    init_server()
