import socket
import os
import configparser


def verify_if_file_exists(filename):
    return os.path.isfile(filename)


def delete(server):
    server.setblocking(1)
    file = str(input('Digite o nome do arquivo (apenas o nome, sem o caminho): '))

    server.send("get_last_id".encode())
    last_id = int(server.recv(256).decode()) + 1
    headers = 'delete;id:' + str(last_id) + ';filename:' + file

    server.send(headers.encode())
    answer = server.recv(1024).decode()

    write_history(str(last_id), answer)


def upload_or_update(server, action):
    file = str(input('Digite o caminho completo do arquivo: '))

    if verify_if_file_exists(file):
        server.setblocking(1)
        filename = os.path.split(file)[1]
        filesize = os.path.getsize(file)

        server.send('get_last_id'.encode())
        last_id = int(server.recv(256).decode()) + 1
        headers = action + ';id:' + str(last_id) + ';filename:' + filename + ';filesize:' + str(filesize)
        server.send(headers.encode())

        print('Aguardando resposta do server')

        status = server.recv(16).decode()
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
            print(server.recv(1024).decode())
    else:
        print("Arquivo não encontrado. Tente novamente.")


def upload(server):
    upload_or_update(server, "upload")


def update(server):
    upload_or_update(server, "update")


def history(server):
    server.setblocking(1)
    if verify_if_file_exists("history.log"):
        f = open("history.log", "r")

        print("Digite o id que deseja refazer")

        line = f.read(1024)
        while line:
            print(line)
            line = f.read(1024)
        identifier = str(input('Digite o id que deseja refazer: '))

        print("Reenviando id {0} para o servidor".format(identifier))

        header = "id:" + identifier
        server.send(header.encode())

        print("Aguardando resposta do servidor...")
        print("Resposta recebida do servidor, referente ao request com id {0}:".format(identifier))
        print(server.recv(1024).decode())

    else:
        print("Não foram realizadas operações anteriores")


def shutdown():
    print("Obrigado por usar. Vá tomar no cu.")
    exit(1)


def switch(choice, server):
    if choice == 'u':
        upload(server)
    elif choice == 'd':
        delete(server)
    elif choice == 'a':
        update(server)
    elif choice == 'h':
        history(server)
    elif choice == 's':
        shutdown()
    else:
        return 'Escolha não valida. Tente novamente'


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

    while True:
        if is_socket_closed(server):
            print("Conexão com o servidor fechada. Necessário reiniciar aplicação")
            break
        else:
            print('''
                Menu:
        
                [u] - Fazer upload de arquivo
                [d] - Deletar arquivo
                [a] - Atualizar arquivo
                [h] - Refazer operação
                [s] - Sair
                ''')
            choice = str(input('Escolha uma opção: '))
            switch(choice, server)


def connect():
    config = configparser.RawConfigParser()
    config.read('ips.conf')

    details_dict = dict(config.items('master'))

    server_ip = details_dict['ip']
    server_port = details_dict['port']

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((server_ip, int(server_port)))
    return server


def init():
    server = ''
    try:
        server = connect()
        menu(server)
    except socket.error as e:
        print("Erro ao tentar conectar com o servidor", str(e))
    finally:
        server.close()


def write_history(id_request, action):
    f = open("history.log", "a+")
    log = str(id_request) + " - " + str(action) + "\n"
    f.write(log)
    f.flush()
    f.close()


if __name__ == '__main__':
    init()
