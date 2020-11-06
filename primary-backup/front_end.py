import sys
import os
import socket

SERVER_IP = '127.0.0.1'
SERVER_PORT = 8882

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.connect((SERVER_IP, SERVER_PORT))
except socket.error as msg:
    print(msg)


