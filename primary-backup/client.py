import socket
import os
import configparser
import sys
import getopt


def pass_args():
    server = connect()
    argv = sys.argv[1:]

    opts = getopt.getopt(argv, 'u:d:s')

    arg_length = 0
    args = opts[0]

    while arg_length < len(opts[0]):
        arg = args[arg_length]
        switch(arg[0], server, arg[1], None)
        arg_length += 1


def init():
    try:
        server = connect()
        menu(server)
    except socket.error as e:
        print("Erro ao tentar conectar com o servidor", str(e))
        print("Tentando conexão novamente")
        init()


def connect():
    config = configparser.RawConfigParser()
    config.read('ips.conf')

    details_dict = dict(config.items('front'))

    server_ip = details_dict['ip']
    server_port = details_dict['port']

    print(f"Tentando iniciar conexão com o front-end no host {server_ip} e porta {server_port}")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.settimeout(30)
    server.connect((server_ip, int(server_port)))

    print("Conexão com o front-end estabelecida com sucesso!")
    return server


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


def print_menu(is_detailed):
    if not is_detailed:
        print('''
|------------------------------------------|
        Menu:

        [u] - Fazer upload de arquivo
        [d] - Deletar arquivo
        [h] - Histórico
        [t] - Menu Detalhado
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
        
        [h] - Exibir o histórico das operações já realizadas
        
        [s] - Sair: Termina o programa.

        [t] Retornar ao menu Simplificado.
|------------------------------------------------------------------------------------------------------------|
                ''')


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


def verify_if_file_exists(filename):
    return os.path.isfile(filename)


def shutdown(server):
    print("Obrigado por usar.")
    server.close()
    exit(1)


def upload(server, path):
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

        header = 'filename:' + filename + ';' + str(filesize)
        server.send(header.encode())

        print('Aguardando resposta do server')

        f = open(file, "rb")

        line = f.read(1024)
        while line:
            server.send(line)
            line = f.read(1024)
        f.close()

        print("Upload completo")

        answer = server.recv(1024).decode()
        print(answer)

        server.setblocking(0)
    else:
        print("Arquivo não encontrado. Tente novamente.")


def delete(server, path):
    server.setblocking(1)

    print("Iniciando processo de deletar arquivos...")

    if path is None:
        file = str(input('Digite o nome do arquivo (apenas o nome, sem o caminho): '))
    else:
        file = path

    print(f"O arquivo a ser deletado é {file}")

    headers = 'delete:' + file

    server.send(headers.encode())
    answer = server.recv(1024).decode()
    print(answer)

    server.setblocking(0)


def view_history(server):
    print("Visualizando operações antigas...")

    server.setblocking(1)

    server.send(b'history')
    size = int(server.recv(32))
    server.send(b'OK')

    receive = 0
    while receive < size:
        line = server.recv(1024)
        print(line.decode())
        receive += len(line)

    server.setblocking(0)


def switch(choice, server, argv, is_detailed):
    if choice == 'u' or choice == '-u':
        upload(server, argv)
    elif choice == 'd' or choice == '-d':
        delete(server, argv)
    elif choice == 't' or choice == '-t':
        return not is_detailed
    elif choice == 's' or choice == '-s':
        shutdown(server)
    elif choice == 'h' or choice == '-h':
        view_history(server)
    else:
        print('Escolha não válida. Tente novamente')
    return is_detailed


if __name__ == '__main__':
    if len(sys.argv) == 1:
        init()
    else:
        pass_args()
