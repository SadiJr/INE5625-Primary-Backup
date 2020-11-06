import socket
import sys
import os
import logging

#TODO Adicionar configurações de servidor e porta em um
# arquivo de configuração

HOST = '127.0.0.1'
PORT = 8882

def verify_if_file_exists(filename):
    return os.path.isfile(filename)

def init_log():
    logging.basicConfig(filename='updates.log', encoding='utf-8', level=logging.INFO)


def verify_if_request_exists(request_id, con):
	splt_char = ';'
	
    with open('updates.log','r') as f:
    	lines = f.read().split("\n")
    	
    for i, line in enumerate(lines):
    	if identifier in line:
    		print('Request já realizado, com a resposta sendo %s', line)
    		temp = line.split(splt_char)
    		answer = splt_char.join(temp[2:])
    		con.send(answer)
    		return True
    
    return False
    		
def write_log(client_id, anwser):
    # Formato do arquivo de log:
    # "Id do request do cliente","resposta do servidor"
    #TODO estudar a possibilidade de adicionar datas ao log.

    logging.info('%s,%s', client_id, anwser)


def send_data_to_slave(data):
    print('Falta fazer')
	
	
def conn(con, client):
    print('Iniciando conexão com o cliente %s', client)
    
    first_message = True
    identifier = ''
    answer = ''

    while True:
        message = con.recs(1024)
        if not message:
            break

	print('Mensagem recebida do cliente %s: %s', client, message)
		
        if first_message:
            first_message = False
            identifier = message
            
            if(verify_if_request_exists(identifier, con)):
            	break
        sockfile = con.makefile('r')
        filename = sockfile.readeline()[:-1]
        
        try:
            file = open(filename, 'wb')
            while True:
                data = con.recv(1024)
                if not data: break
                file.write(data)
        		
            send_data_to_slaves(file)
        except:
            print('Um erro ocorreu com o arquivo %s', filename)	
    print('Finalizando conexão com o cliente %s', client)
    con.close()

def init_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (HOST, PORT)

    try:
        sock.bind(server_address)
    except socket.error as msg:
        print('Erro ao fazer o bind do socket. Código do Erro: %s - Mensagem: %s', msg[0], msg[1])
        sys.exit()

    print('Iniciando servidor com o IP %s na porta %s' % sock.getsockname())
    sock.listen(1)

    while True:
        print('Esperando conexões')
        connection, client = sock.accept()
        conn(connection, client)
    sock.close()

if __name__ == '__main__':
    init_server()
