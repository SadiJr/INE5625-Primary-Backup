import socket

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8882


def delete():
    print('Falta fazer')


def upload():
    print('Falta fazer')


def update():
    print('Falta fazer')


def history():
    print('Falta fazer')


def shutdown():
    print("Obrigado por usar. Vá tomar no cu.")
    exit(1)


def switch(choice):
    if choice == 'u':
        upload()
    elif choice == 'd':
        delete()
    elif choice == 'a':
        update()
    elif choice == 'h':
        history()
    elif choice == 's':
        shutdown()
    else:
        return 'Escolha não valida. Tente novamente'


def menu():
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
        switch(choice)


def connect():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((SERVER_IP, SERVER_PORT))
    return server


def send_file():
    try:
        server = connect()

        menu()

        server.send('get_last_id'.encode('utf-8'))
        last_id = int(server.recv(256).decode('utf-8')) + 1
        print('Last Id é ' + str(last_id))

        filename = 'teste.txt'
        headers = 'id:' + str(last_id) + '\nfilename:' + filename + '\n'
        server.send(headers.encode('utf-8'))

        print('Aguardando resposta do server')
        f = open("teste.txt", "rb")

        line = f.read(1024)
        while line:
            server.send(line)
            line = f.read(1024)

    except socket.error as e:
        print("Erro ao tentar conectar com o servidor")
    finally:
        server.close()


if __name__ == '__main__':
    send_file()
