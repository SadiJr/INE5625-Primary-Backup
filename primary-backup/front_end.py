import socket
import os

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8882


def verify_if_file_exists(filename):
    return os.path.isfile(filename)


def delete(server):
    print('Falta fazer')

    write_history(1, 'Deletar')


def upload(server):
    file = str(input('Digite o caminho completo do arquivo: '))

    if verify_if_file_exists(file):
        filename = os.path.split(file)[1]
        print(filename)
        server.send('get_last_id'.encode('utf-8'))
        last_id = int(server.recv(256).decode('utf-8')) + 1
        print('Last Id é ' + str(last_id))
        headers = 'id:' + str(last_id) + '\nfilename:' + filename
        server.send(headers.encode('utf-8') + b"")
        status = server.recv(16).decode('UTF-8')

        if status == "OK":
            print('Aguardando resposta do server')

            f = open(file, "rb")
            line = f.read(1024)
            while line:
                server.send(line)
                line = f.read(1024)
            f.close()
            server.send(b"DONE")
            print("Upload completo")
            answer = server.recv(1024)
            print(answer)

            write_history(last_id, "Upload de arquivo")
        else:
            print("Ocorreu um erro.")
    else:
        print("Arquivo não encontrado. Tente novamente.")


def update(server):
    print("Falta fazer")


def history(server):
    print('Falta fazer')


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


def menu(server):
    while True:
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
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((SERVER_IP, SERVER_PORT))
    return server


def send_file():
    try:
        server = connect()
        menu(server)
    except socket.error as e:
        print("Erro ao tentar conectar com o servidor")
    finally:
        server.close()


def write_history(id_request, action):
    f = open("history", "a+")
    f.write(str(id_request) + ' - ' + action)


if __name__ == '__main__':
    send_file()
