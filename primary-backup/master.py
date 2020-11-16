import socket
import sys
import os
from pathlib import Path
import configparser
import collections

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
    print(slaves)

    data = list(slaves.values())
    h, p = 0, 1

    for line in range(int((len(data) / 2))):
        host = data[h]
        port = data[p]
        try:
            server = create_slave_server(host, port)
            connections.append(server)
        except ConnectionRefusedError:
            print("Erro ao tentar conectar no servidor {0} na porta {1}".format(host, port))

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
                print("Request já realizado, com a resposta sendo " + line)
                temp = line.split(split_char)
                answer = split_char.join(temp[1:])
                con.send(answer)
                return True
    return False


def write_log(client_id, anwser):
    f = open("updates.log", "a+")
    f.write(client_id + ";" + anwser + "\n")
    f.flush()


def send_data_to_slaves(filename):
    responses = []
    for i in connections:
        conn = socket.socket(i)
        conn.send(filename)
        conn.settimeout(5.0)

        f = open(filename, "rb")
        line = f.read(1024)

        while line:
            conn.send(line)
            line = f.read(1024)

        f.close()
        conn.send(b"DONE")
        responses.append(conn.recv(1024).decode("UTF-8"))
    return responses


def receive_file(connection, filename, identifier, action):
    print("Filename: " + filename + " - id: " + identifier)
    file = open(filename, "wb")

    line = connection.recv(1024)
    while line:
        print("Linha recebida: " + str(line))
        if line.__contains__(b"DONE"):
            break
        file.write(line)
        file.flush()
        line = connection.recv(1024)

    file.close()
    print("Arquivo recebido!")
    answer = send_data_to_slaves(file)
    write_log(identifier, answer)
    print("Log escrito")

    response = "Arquivo " + str(action) + " com sucesso"
    connection.send(response.encode('UTF-8'))


def verify_if_file_exists(filename):
    return os.path.isfile(filename)


def send_delete_request_to_slaves(filename):
    responses = []
    for i in connections:
        conn = socket.socket(i)
        message = "delete;" + filename
        conn.send(message.encode("UTF-8"))
        conn.settimeout(5.0)

        responses.append(conn.recv(1024).decode("UTF-8"))

    return responses


def delete(connection, data):
    identifier = str(data).split(';')[1].split(':')[1]
    filename = str(data).split(';')[2].split(':')[1]

    if verify_if_request_exists(identifier, connection):
        connection.close()
    elif verify_if_file_exists(filename):
        os.remove(filename)

        responses = send_delete_request_to_slaves(filename)
        if len(responses) < len(connection / 2):
            # TODO Verificar qual será a lógica de negócio aplicada para esse tipo de situação
            connection.send("A maioria dos servivores de backup caiu, "
                            "infelizmente teremos de abortar sua requisição".encode("UTF-8"))
        else:
            connection.send("Arquivo deletado com sucesso".encode("UTF-8"))
    else:
        connection.send("Arquivo não existente no servidor".encode("UTF-8"))
        connection.close()


def get_last_id():
    if verify_if_log_exists():
        with open("updates.log", "r") as f:
            lines = f.read().splitlines()
            last_line = lines[-1]
            identifier = last_line.split(";")[0]
            return int(identifier)
    return 0


def upload_or_update(connection, message):
    identifier, filename = "", ""
    for line in message.split(";"):
        if line.startswith("id:"):
            identifier = line.split(":")[1]
        elif line.startswith("filename:"):
            filename = line.split(":")[1]

    if verify_if_request_exists(identifier, connection):
        connection.close()
    else:
        if message.__contains__("update"):
            action = "atualizado"
        else:
            action = "criado"
            if verify_if_file_exists(filename):
                connection.send("Arquivo já criado! Utilize a opção atualizar".encode("UTF-8"))
                return

        connection.send("OK".encode('UTF-8'))
        receive_file(connection, filename, identifier, action)


def connect(connection, client):
    print("Iniciando conexão com o cliente ", client)

    while True:
        message = connection.recv(256).decode("utf-8")

        print("Mensagem recebida do cliente: " + message)
        if not message:
            return

        if message == "get_last_id":
            connection.send(str(get_last_id()).encode("utf-8"))
            continue

        if message.__contains__("delete"):
            delete(connection, message)
        elif message.__contains__("update") | message.__contains__("upload"):
            upload_or_update(connection, message)
        else:
            connection.send("Erros na requisição. Vai tomar no cu".encode("UTF-8"))
            connection.close()
            break

        if int(message.split(";")[1].split(":")[1]) % 10 == 0:
            send_log_to_slaves()

    print("Finalizando conexão com o cliente")


def send_log_to_slaves():
    conn = ""
    for i in connections:
        try:
            conn = socket.socket(i)
            conn.send("history".encode("UTF-8"))

            f = open("updates.log", "rb")
            line = f.read(1024)

            while line:
                conn.send(line)
                line = f.read(1024)
            f.close()
            conn.send(b"DONE")
        except Exception as e:
            print(type(e))
            print("Erro ao mandar arquivo de log para o backup {0}".format(conn.getsockname()))


def init_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    config_dict = get_config_section()
    host = config_dict['master']['ip']
    port = config_dict['master']['port']

    server_address = (host, int(port))

    try:
        sock.bind(server_address)
    except socket.error as msg:
        print("Erro ao fazer o bind do socket. Código do Erro: %s - Mensagem: %s", msg[0], msg[1])
        sys.exit()

    print("Iniciando servidor com o IP %s na porta %s" % sock.getsockname())
    sock.listen(1)

    connected_slaves_count = connect_to_slaves()

    #if len(connections) < (connected_slaves_count / 2):
    #   print("Mais da metade dos servidores de backup está fora do ar. Abortando...")
    #   sys.exit(0)

    while True:
        try:
            print("Esperando conexões")
            connection, client = sock.accept()
            connect(connection, client)
        except Exception as e:
            print("Deu ruim: ", str(e.__traceback__))
            connection.close()
            sock.close()


if __name__ == "__main__":
    init_server()
