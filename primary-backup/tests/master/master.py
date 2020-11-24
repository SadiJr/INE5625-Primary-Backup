import socket
import sys
import os
from builtins import print
from pathlib import Path
import configparser
import collections
import tempfile
from shutil import copyfile

config = configparser.RawConfigParser()
config.read('ips.conf')
connections = []
tempdir = tempfile.TemporaryDirectory()


def remove_tmp_files():
    for file in os.listdir(tempdir.name):
        os.remove(tempdir.name + os.path.sep + file)


def rollback():
    print(f"Realizando rollback...")
    for file in os.listdir(tempdir.name):
        copyfile((tempdir.name + os.path.sep + file), (os.path.abspath(os.path.curdir) + os.path.sep + file))
    print("Rollaback realizado com sucesso! Limpando diretório temporário")
    remove_tmp_files()

    for conn in connections:
        print(f"Enviando ordem de rollback para {conn.getsockname()}")

        try:
            message = f"rollback"
            conn.send(message.encode())
            conn.settimeout(5.0)
        except Exception:
            print("Erro ao tentar enviar request de rollback para o servidor {0}".format(conn.getsockname()))


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
                print("Request já realizado, com a resposta sendo:\n" + answer)
                con.send(answer.encode())
                return True
    return False


def write_log(client_id, answer):
    f = open("updates.log", "a+")
    f.write(str(client_id) + ";" + str(answer) + "\n")
    f.flush()


def send_data_to_slaves(filename, filesize, identifier):
    print(f"Enviando arquivo {filename} para os slaves")
    responses = []
    for conn in connections:
        try:
            header = f"{filename};{filesize};{identifier}"
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
        if a == "500" or a == '':
            fail += 1
        else:
            success += 1

    return success, fail


def receive_file(connection, filename, filesize, identifier, action):
    try:
        print(f"Iniciando backup do arquivo original {filename}, caso exista...")
        copyfile(filename, (tempdir.name + os.path.sep + filename))
        print("Backup realizado com sucesso!")
    except FileNotFoundError:
        print(f"Arquivo {filename} não encontrado no servidor, não será  realizada cópia de segurança!")

    file = open(filename, "wb")
    receive_size = 0

    print(f"Iniciando recepção do arquivo {filename}")

    while receive_size != filesize:
        line = connection.recv(1024)
        if not line:
            break

        file.write(line)
        receive_size += len(line)

    file.flush()
    file.close()

    print(f"Arquivo {filename} recebido com sucesso!")

    answer = send_data_to_slaves(filename, filesize, identifier)
    status = verify_slaves_success(answer)

    if len(answer) < (len(connections) / 2) or status[0] < status[1]:
        print("Erro ao receber respostas dos slaves. Abortando operação...")
        if action == "criado":
            os.remove(filename)
            send_delete_request_to_slaves(filename, identifier)
        else:
            rollback()
        connection.send("Erro ao realizar transição. Tente novamente".encode())
        return

    response = f"Arquivo {filename} {action} com sucesso"
    write_log(identifier, response)
    connection.send(response.encode())


def verify_if_file_exists(filename):
    return os.path.isfile(filename)


def send_delete_request_to_slaves(filename, identifier):
    print("Enviando ordens aos slaves para deletar o arquivo {0}".format(filename))

    responses = []
    for conn in connections:
        try:
            message = f"delete;{filename};{identifier}"
            conn.send(message.encode())

            responses.append(conn.recv(1024).decode())
        except Exception:
            print("Erro ao tentar enviar request de delete para o servidor {0}".format(conn.getsockname()))

    return responses


def delete(connection, data):
    remove_tmp_files()

    identifier = str(data).split(';')[1].split(':')[1]
    filename = str(data).split(';')[2].split(':')[1]

    print(f"Arquivo a ser deletado: {filename}, com o identificador da transação sendo {identifier}")

    if not verify_if_request_exists(identifier, connection):
        if verify_if_file_exists(filename):

            print(f"Fazendo backup do arquivo {filename} em um diretório temporário para necessidade de rollback!")
            copyfile(filename, (tempdir.name + os.path.sep + filename))

            os.remove(filename)

            responses = send_delete_request_to_slaves(filename, identifier)

            status = verify_slaves_success(responses)
            if len(responses) < (len(connections) / 2) or status[0] < status[1]:
                print("A maioria dos servidores de backup não respondeu a requisição de deletar o arquivo "
                      " ou respondeu com erro na operação")

                rollback()
                error_message = f"Erro ao realizar operação de deletar o arquivo {filename}"
                connection.send(error_message.encode())
            else:
                message = f"Arquivo {filename} deletado com sucesso"
                connection.send(message.encode())
        else:
            print("O arquivo {0} não existe no servidor! Abortando operação.".format(filename))
            message = f"Arquivo {filename} não encontrado no servidor."
            connection.send(message.encode())


def get_last_id():
    if verify_if_log_exists():
        with open("updates.log", "r") as f:
            lines = f.read().splitlines()
            last_line = lines[-1]
            identifier = last_line.split(";")[0]
            return int(identifier)
    return 0


def upload_or_update(connection, message):
    remove_tmp_files()

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
            if not verify_if_file_exists(filename):
                connection.send("Arquivo ainda não criado. Utilize a opção de upload".encode())
                return
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

        elif message.__contains__("id:"):
            print("Verificando se a requisição já foi processada...")
            identifier = message.split(":")[1]

            if verify_if_request_exists(identifier, connection):
                print("Request {0} já arquivado e resposta já enviada ao cliente".format(identifier))
                continue
            else:
                print("Erro ao tentar encontrar id {0} no registro de logs.".format(identifier))
                sys.exit(0)
        elif message.__contains__("verify_file:"):
            filename = message.split(':')[1]
            if verify_if_file_exists(filename):
                result = b"0";
            else:
                result = b"1"
            connection.send(result)
            continue
        else:
            connection.send("Erros na requisição".encode())
            connection.close()
            break

        # Isso é desnecessário
        #if int(message.split(";")[1].split(":")[1]) % 10 == 0:
        #    send_log_to_slaves()

    print("Finalizando conexão com o cliente")


def send_log_to_slaves():
    for conn in connections:
        try:
            filesize = os.path.getsize("updates.log")

            header = f"history;{filesize}"
            conn.send(header.encode())

            status = conn.recv(16).decode()

            if status == "OK":
                f = open("updates.log", "rb")
                line = f.read(1024)

                while line:
                    conn.send(line)
                    line = f.read(1024)
                f.close()
            else:
                print("Erro ao mandar arquivo de log para o backup {0}".format(conn.getsockname()))
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
        print("Erro ao fazer o bind do socket. Porta já ocupada")
        sys.exit()

    print(f"Diretório temporário {tempdir} será usado para tratar rollbacks")

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
            connection.close()


if __name__ == "__main__":
    init_server()
