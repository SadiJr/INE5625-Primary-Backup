import socket
import sys
import os
from builtins import print
from pathlib import Path
import configparser
import collections
import traceback

config = configparser.RawConfigParser()
config.read('ips.conf')
connections = []


def get_config_section():
    if not hasattr(get_config_section, 'section_dict'):
        get_config_section.section_dict = collections.defaultdict()

        for section in config.sections():
            get_config_section.section_dict[section] = dict(config.items(section))

    return get_config_section.section_dict


def create_slave_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, int(port)))
    return server


def connect_to_slaves():
    slaves = dict(config.items('slaves'))

    data = list(slaves.values())
    h, p = 0, 1

    for line in range(int((len(data) / 2))):
        host = data[h]
        port = data[p]
        try:
            server = create_slave_server(host, port)
            connections.append(server)
            print("Conexão estabelecida com o slave {0} no host {1} na porta {2}".format(line, host, port))
        except ConnectionRefusedError:
            print("Erro ao tentar conectar ao slave {0}  no host {1} na porta {2}".format(line, host, port))

        h += 2
        p += 2

    return int((len(data) / 2))


def verify_if_log_exists():
    file = Path("updates.log")
    if file.is_file() and os.stat("updates.log").st_size > 0:
        return True
    return False


def verify_if_request_exists(request_id, con):
    if verify_if_log_exists():
        split_char = ";"

        with open("updates.log", "r") as f:
            lines = f.read().split("\n")

        for line in lines:
            if request_id in line.split(split_char)[0]:
                temp = line.split(split_char)
                answer = split_char.join(temp[1:])
                print("Request já realizado, com a resposta sendo " + answer)
                con.send(answer)
                return True
    return False


def write_log(client_id, answer):
    f = open("updates.log", "a+")
    f.write(str(client_id) + ";" + str(answer) + "\n")
    f.flush()


def send_data_to_slaves(filename, filesize):
    responses = []
    for conn in connections:
        try:
            header = f"{filename};{filesize}"
            conn.send(header.encode())
            # conn.settimeout(5.0)
            response = conn.recv(16).decode()

            if response == "OK":
                f = open(filename, "rb")

                line = f.read(1024)
                while line:
                    conn.send(line)
                    line = f.read(1024)
                f.close()
                responses.append(conn.recv(1024).decode())
            else:
                print("Erro ao enviar arquivo para o escravo {0}".format(conn.getsockname()))

        except Exception:
            print("Erro ao enviar arquivo para o escravo {0}".format(conn.getsockname()))
    return responses


def verify_slaves_success(answers):
    success, fail = 0, 0

    for a in answers:
        if a == "500":
            fail += 1
        else:
            success += 1

    return success, fail


def receive_file(connection, filename, filesize, identifier, action):
    print("Filename: " + filename + " - id: " + identifier + " - filesize: " + str(filesize))
    file = open(filename, "wb")

    receive_size = 0

    while receive_size != filesize:

        line = connection.recv(1024)
        if not line:
            break

        file.write(line)
        receive_size += len(line)

    file.flush()
    file.close()
    print("Arquivo recebido!")
    answer = send_data_to_slaves(filename, filesize)

    status = verify_slaves_success(answer)

    if len(answer) < (len(connections) / 2) or status[0] < status[1]:
        print("Erro ao receber respostas dos slaves. Abortando operação...")
        connection.send("Erro ao realizar transição. Tente novamente".encode())
        return

    response = "Arquivo " + str(action) + " com sucesso"
    write_log(identifier, response)

    connection.send(response.encode())


def verify_if_file_exists(filename):
    return os.path.isfile(filename)


def send_delete_request_to_slaves(filename):
    print("Enviando ordens aos slaves para deletar o arquivo {0}".format(filename))

    responses = []
    for conn in connections:
        try:
            message = "delete;" + filename
            conn.send(message.encode())
            conn.settimeout(5.0)

            responses.append(conn.recv(1024).decode())
        except Exception:
            print("Erro ao tentar enviar request de delete para o servidor {0}".format(conn.getsockname()))

    return responses


def delete(connection, data):
    identifier = str(data).split(';')[1].split(':')[1]
    filename = str(data).split(';')[2].split(':')[1]

    print("Arquivo a ser deletado: {0}".format(filename))

    if not verify_if_request_exists(identifier, connection):
        if verify_if_file_exists(filename):
            os.remove(filename)

            responses = send_delete_request_to_slaves(filename)

            status = verify_slaves_success(responses)
            if len(responses) < (len(connections) / 2) or status[0] < status[1]:
                print("A maioria dos servidores de backup não respondeu a requisição de deletar o arquivo "
                      " ou respondeu com erro na operação")
                connection.send("Erro ao realizar operação de deletar o arquivo".encode())
            else:
                connection.send("Arquivo deletado com sucesso".encode())
        else:
            print("O arquivo {0} não existe no servidor! Abortando operação.".format(filename))
            connection.send("Arquivo não existente no servidor".encode())


def get_last_id():
    if verify_if_log_exists():
        with open("updates.log", "r") as f:
            lines = f.read().splitlines()
            last_line = lines[-1]
            identifier = last_line.split(";")[0]
            return int(identifier)
    return 0


def upload_or_update(connection, message):
    identifier, filename,  = "", ""
    filesize = 0

    for line in message.split(";"):
        if line.startswith("id:"):
            identifier = line.split(":")[1]
        elif line.startswith("filename:"):
            filename = line.split(":")[1]
        elif line.startswith("filesize"):
            filesize = int(line.split(':')[1])

    if not verify_if_request_exists(identifier, connection):
        if message.__contains__("update"):
            action = "atualizado"
        else:
            action = "criado"
            if verify_if_file_exists(filename):
                connection.send("Arquivo já criado! Utilize a opção atualizar".encode())
                return

        connection.send("OK".encode())
        receive_file(connection, filename, filesize, identifier, action)


def connect(connection, client):
    print("Iniciando conexão com o cliente {0}".format(client))

    while True:
        print("Esperando requests do front-end...")

        message = connection.recv(256).decode()

        if message == b'' or message == '' or not message:
            print("Erro na conexão com o front-end! Voltando a esperar nova conexão com o master")
            connection.close()
            break

        print("Mensagem recebida do cliente: " + message)

        if message == "get_last_id":
            print("Enviando ao front-end o id da última operação realizada")
            connection.send(str(get_last_id()).encode())
            continue

        if message.__contains__("delete"):
            print("Iniciando processo de deletar um arquivo...")
            delete(connection, message)
        elif message.__contains__("update") | message.__contains__("upload"):
            upload_or_update(connection, message)
        else:
            connection.send("Erros na requisição".encode())
            connection.close()
            break

        if int(message.split(";")[1].split(":")[1]) % 10 == 0:
            send_log_to_slaves()

    print("Finalizando conexão com o cliente")


def send_log_to_slaves():
    for conn in connections:
        try:
            filesize = os.path.getsize("updates.log")

            header = f"history;{filesize}"
            conn.send(header.encode())

            f = open("updates.log", "rb")
            line = f.read(1024)

            while line:
                conn.send(line)
                line = f.read(1024)
            f.close()
        except Exception:
            print("Erro ao mandar arquivo de log para o backup {0}".format(conn.getsockname()))


def init_server():
    print("Iniciando servidor...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    config_dict = get_config_section()
    host = config_dict['master']['ip']
    port = config_dict['master']['port']

    print("Lendo configurações do servidor. O host é {0} e a porta {1}".format(host, port))
    server_address = (host, int(port))

    try:
        print("Iniciando servidor no host {0} na porta {1}".format(host, port))
        sock.bind(server_address)
    except socket.error as msg:
        print("Erro ao fazer o bind do socket. Código do Erro: {0} - Mensagem: {1}".format(msg[0], msg[1]))
        print("Tentando reiniciar servidor")
        init_server()
        return

    sock.listen(1)

    print("Iniciando conexão com o(s) slave(s)")
    connected_slaves_count = connect_to_slaves()

    if len(connections) < (connected_slaves_count / 2):
        print("Mais da metade dos servidores de backup está fora do ar. Abortando...")
        sys.exit(0)

    while True:
        try:
            print("Esperando conexões")
            connection, client = sock.accept()
            connect(connection, client)
        except Exception:
            traceback.print_exc()
            connection.close()
            init_server()


if __name__ == "__main__":
    init_server()
