import socket
import configparser
from builtins import print
import sys
import collections
import tempfile
import traceback
import os


config = configparser.RawConfigParser()
config.read('ips.conf')


def write_history(result):
    f = open("history.log", "a+")
    log = str(result) + "\n"
    f.write(log)
    f.flush()
    f.close()


def send_history(client):
    f = open('history.log', 'rb')
    line = f.read(1024)
    while line:
        client.send(line)
        line = f.read(1024)


def get_config_section():
    if not hasattr(get_config_section, 'section_dict'):
        get_config_section.section_dict = collections.defaultdict()

        for section in config.sections():
            get_config_section.section_dict[section] = dict(config.items(section))

    return get_config_section.section_dict


def user_connection(connection, client, master):
    print("Iniciando conexão com o cliente {0}".format(client))

    while True:
        print("Esperando requests do client...")

        message = connection.recv(256).decode()

        if message == b'' or message == '' or not message:
            print("Erro na conexão com o cliente! Voltando a esperar novas conexões")
            connection.close()
            break
        else:
            treat_message(connection, message, master)


def treat_message(client, message, master):
    master.send(b"get_last_id")
    identifier = int(master.recv(16)) + 1

    print(message)
    if message.__contains__("filename:"):
        filename = message.split(';')[0].split(':')[1]
        filesize = int(message.split(';')[1])

        receive = 0
        with tempfile.NamedTemporaryFile() as tmpfile:
            try:
                while receive < filesize:
                    data = client.recv(1024)
                    tmpfile.write(data)
                    receive += len(data)

            except:
                traceback.print_exc()
            tmpfile.flush()

            client.send(send_to_master(tmpfile, identifier, filename, filesize, master).encode())
    elif message.__eq__("history"):
        size = str(os.path.getsize('history.log'))
        client.send(size.encode())

        if client.recv(16).decode() == "OK":
            send_history(client)
        else:
            print("Erro ao realizar a operação!")
            client.close()

    else:
        filename = message.split(':')[1]
        header = message.split(':')[0] + ';id:' + str(identifier) + ';filename:' + filename

        master.send(header.encode())
        result = master.recv(1024)
        write_history(result)
        client.send(result)


def send_to_master(tmpfile, identifier, filename, filesize, master):
    verify = "verify_file:" + filename
    master.send(verify.encode())

    if int(master.recv(26).decode()) == 0:
        headers = 'update;id:' + str(identifier) + ';filename:' + filename + ';filesize:' + str(filesize)
    else:
        headers = 'upload;id:' + str(identifier) + ';filename:' + filename + ';filesize:' + str(filesize)

    master.send(headers.encode())
    status = master.recv(16).decode()
    if status == "OK":
        upload_file_to_master(tmpfile, master)
        result = master.recv(1024).decode()
        write_history(result)
        return result
    else:
        print(status)
        return "Ocorreu um erro inesperado. Favor contatar o suporte."


def upload_file_to_master(tmpfile, master):
    f = open(tmpfile.name, 'rb')
    line = f.read(1024)
    while line:
        master.send(line)
        line = f.read(1024)


def connect_to_master():
    details_dict = dict(config.items('master'))

    server_ip = details_dict['ip']
    server_port = details_dict['port']

    print("Tentando iniciar conexão com o master no host {0} e porta {1}".format(server_ip, server_port))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.settimeout(10)
    server.connect((server_ip, int(server_port)))

    print("Conexão com o master estabelecida com sucesso!")
    return server


def init():
    print("Iniciando servidor...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    config_dict = get_config_section()
    host = config_dict['front']['ip']
    port = config_dict['front']['port']

    print(f"Lendo configurações do servidor. O host é {host} e a porta {port}")
    server_address = (host, int(port))

    try:
        print("Iniciando servidor no host {0} na porta {1}".format(host, port))
        sock.bind(server_address)
    except socket.error as msg:
        print("Erro ao fazer o bind do socket. Porta já ocupada")
        sys.exit()

    master = connect_to_master()

    sock.listen()
    while True:
        try:
            print("Esperando conexões")
            connection, client = sock.accept()
            user_connection(connection, client, master)
        except Exception:
            connection.close()
            traceback.print_exc()


if __name__ == "__main__":
    init()