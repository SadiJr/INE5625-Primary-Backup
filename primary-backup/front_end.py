import socket
import os
import configparser
from builtins import print
import sys
import getopt

from tests import test


def verify_if_file_exists(filename):
    return os.path.isfile(filename)


def delete(server, path):
    server.setblocking(1)

    print("Iniciando processo de deletar arquivos...")

    if path is None:
        file = str(input('Digite o nome do arquivo (apenas o nome, sem o caminho): '))
    else:
        file = path

    print(f"O arquivo a ser deletado é {file}")

    server.send("get_last_id".encode())
    last_id = int(server.recv(256).decode()) + 1
    headers = 'delete;id:' + str(last_id) + ';filename:' + file

    server.send(headers.encode())
    answer = server.recv(1024).decode()
    print(answer)

    write_history(str(last_id), answer)
    server.setblocking(0)


def upload_or_update(server, action, path):
    if path is None:
        file = str(input('Digite o caminho completo do arquivo: '))
    else:
        file = path

    while not verify_if_file_exists(file):
        file = str(input("Arquivo não encontrado. Tente novamente: "))

    if verify_if_file_exists(file):
        server.setblocking(1)
        filename = os.path.split(file)[1]
        filesize = os.path.getsize(file)

        server.send('get_last_id'.encode())
        last_id = int(server.recv(256).decode()) + 1
        headers = action + ';id:' + str(last_id) + ';filename:' + filename + ';filesize:' + str(filesize)
        server.send(headers.encode())

        print('Aguardando resposta do server')

        status = server.recv(1024).decode()
        if status == "OK":
            f = open(file, "rb")

            line = f.read(1024)
            while line:
                server.send(line)
                line = f.read(1024)
            f.close()

            print("Upload completo")

            answer = server.recv(1024).decode()
            print(answer)

            write_history(last_id, answer)
        else:
            print("Request já realizado. Resultado: ")
            print(status)
        server.setblocking(0)
    else:
        print("Arquivo não encontrado. Tente novamente.")


def upload(server, argv):
    print("Iniciando processo de upload")
    upload_or_update(server, "upload", argv)


def update(server, argv):
    print("Iniciando processo de update")
    upload_or_update(server, "update", argv)


def history(server, user_id):
    print("Verificando operações já feitas...")

    server.setblocking(1)
    if verify_if_file_exists("history.log"):
        f = open("history.log", "r")

        print("Lendo os logs do cliente...\n")

        line = f.read(1024)
        while line:
            print(line)
            line = f.read(1024)

        if user_id is None:
            identifier = str(input('Digite o id que deseja refazer: '))
        else:
            identifier = user_id

        print("Reenviando id {0} para o servidor".format(identifier))

        header = "id:" + identifier
        server.send(header.encode())

        print("Aguardando resposta do servidor...")
        print("Resposta recebida do servidor, referente ao request com id {0}:".format(identifier))
        print(server.recv(1024).decode())

    else:
        print("Não foram realizadas operações anteriores")
    server.setblocking(0)


def shutdown(server):
    print("Obrigado por usar.")
    server.close()
    exit(1)


def switch(choice, server, argv, is_detailed):
    if choice == 'u' or choice == '-u':
        upload(server, argv)
    elif choice == 'd' or choice == '-d':
        delete(server, argv)
    elif choice == 'a' or choice == '-a':
        update(server, argv)
    elif choice == 't' or choice == '-t':
        return not is_detailed
    elif choice == 'r' or choice == '-r':
        print("Rodando Testes Unitários")
        os.system('python tests/test.py')
    elif choice == 'h' or choice == '-h':
        history(server, argv)
    elif choice == 's' or choice == '-s':
        shutdown(server)
    else:
        print('Escolha não válida. Tente novamente')
    return is_detailed


def details():
    return 1+1


def is_socket_closed(sock) -> bool:
    try:
        # this will try to read bytes without blocking and also without removing them from buffer (peek only)
        sock.setblocking(0)
        data = sock.recv(16, socket.MSG_PEEK)
        if len(data) == 0:
            return True
    except BlockingIOError:
        return False  # socket is open and reading from it would block
    except ConnectionResetError:
        return True  # socket was closed for some other reason
    return False


def menu(server):
    is_detailed = False
    while True:
        if is_socket_closed(server):
            print("Conexão com o servidor fechada. Necessário reiniciar aplicação")
            break
        else:
            print_menu(is_detailed)
            choice = str(input('Escolha uma opção: '))
            is_detailed = switch(choice, server, None, is_detailed)


def print_menu(is_detailed):
    if not is_detailed:
        print('''
|------------------------------------------|
        Menu:

        [u] - Fazer upload de arquivo
        [d] - Deletar arquivo
        [a] - Atualizar arquivo
        [h] - Refazer operação
        [t] - Menu Detalhado
        [r] - Rodar Testes Unitários
        [s] - Sair
|------------------------------------------|
                ''')
    else:
        print('''
|------------------------------------------------------------------------------------------------------------|
        Menu:

        [u] - Fazer upload de arquivo: Permite o envio de um arquivo para o servidor e seus backups. 
        Requer a indicação do caminho do arquivo desejado.
        
        [d] - Deletar arquivo: Deleta o arquivo do servidor e de todos seus backups. 
        Não deleta sua cópia do arquivo.
        
        [a] - Atualiza arquivo já presente no servidor e backups. Similar ao upload, 
        mas para um arquivo que já exista.
        
        [h] - Refazer operação: Permite refazer uma operação realizada previamente, 
        o resultado da opeação já é conhecido, então procesamento é poupado.
        
        [r] - Rodar Testes Unitários: Realiza os testes unitários,para garantir que todas funcionalidades 
        funcionam corretamente. Importante para quando o programa é rodado pela primeira vez em uma máquina.
        
        [s] - Sair: Termina o programa.
        
        [t] Retornar ao menu Simplificado.
|------------------------------------------------------------------------------------------------------------|
                ''')


def connect():
    config = configparser.RawConfigParser()
    config.read('ips.conf')

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
    try:
        server = connect()
        menu(server)
    except socket.error as e:
        print("Erro ao tentar conectar com o servidor", str(e))
        print("Tentando conexão novamente")
        init()


def write_history(id_request, action):
    f = open("history.log", "a+")
    log = str(id_request) + " - " + str(action) + "\n"
    f.write(log)
    f.flush()
    f.close()


def pass_args():
    server = connect()
    argv = sys.argv[1:]

    opts = getopt.getopt(argv, 'u:a:d:h:s')

    arg_length = 0
    args = opts[0]

    while arg_length < len(opts[0]):
        arg = args[arg_length]
        switch(arg[0], server, arg[1], None)
        arg_length += 1


if __name__ == '__main__':
    if len(sys.argv) == 1:
        init()
    else:
        pass_args()
