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
    print("Obrigado por usar.")
    exit(1)


def switch(choice, server, is_detailed):
    if choice == 'u':
        upload(server)
    elif choice == 'd':
        delete(server)
    elif choice == 'a':
        update(server)
    elif choice == 'h':
        history(server)
    elif choice == 't':
        return not is_detailed
    elif choice == 'r':
        # Rodar testes e printar resultados
        print("Rodando Testes Unitários")
    elif choice == 's':
        shutdown()
    else:
        print('Escolha não valida. Tente novamente')
        choice = str(input('Escolha uma opção: '))
        switch(choice, server, is_detailed)
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
            is_detailed = switch(choice, server, is_detailed)


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
