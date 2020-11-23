import sys
import os
import shutil
from sys import executable
from subprocess import Popen
import threading
import importlib.util


def stop_tests():
    delete_dirs()
    sys.exit(0)


def delete_dirs():
    print("Deletando diretórios e arquivos criados durante o teste...")
    try:
        os.remove('tests/front_end.py')
        os.remove('tests/ips.conf')
        shutil.rmtree('tests/master')
        shutil.rmtree('tests/slave1')
        shutil.rmtree('tests/slave2')
        shutil.rmtree('tests/slave3')
    except OSError:
        print("Erro ao deletar arquivos temporários. Abortando...")
        sys.exit()
    print("Remoção de arquivos e diretórios temporários feita com sucesso!")


def create_dirs():
    print("Criando subdiretórios onde ficaram os arquivos replicados...")

    print("Criando diretório do master...")
    try:
        os.mkdir('tests' + os.path.sep + 'master')
    except OSError as error:
        print("Directory master can not be created")
        stop_tests()

    print("Diretório do master criado com sucesso!")

    print("Criando diretórios dos slaves...")

    try:
        os.mkdir('tests' + os.path.sep + 'slave1')
        os.mkdir('tests' + os.path.sep + 'slave2')
        os.mkdir('tests' + os.path.sep + 'slave3')
    except OSError:
        print("Erro ao criar os diretórios dos slaves")
        stop_tests()


def copy_config_files():
    print("Copiando arquivos de configuração")
    try:
        shutil.copy('ips.conf', 'tests')
        shutil.copy('ips.conf', 'tests' + os.path.sep + 'master')
        shutil.copy('slave1.conf', 'tests' + os.path.sep + 'slave1')
        shutil.copy('slave2.conf', 'tests' + os.path.sep + 'slave2')
        shutil.copy('slave3.conf', 'tests' + os.path.sep + 'slave3')
        for i in range(3):
            index = str(i + 1)
            os.rename("tests/slave" + index + "/slave" + index + ".conf", "tests/slave" + index + "/slave.conf")
    except OSError:
        print("Erro ao realizar a cópia dos arquivos de configuração. Abortando...")
        stop_tests()
    print("Cópia realizada com sucesso")


def copy_py_files():
    print("Copiando os arquivos .py do front-end, master e dos slaves para seus respectivos diretórios de teste")

    try:
        shutil.copy('front_end.py', 'tests')
        shutil.copy('master.py', 'tests' + os.path.sep + 'master')
        shutil.copy('slave.py', 'tests' + os.path.sep + 'slave1')
        shutil.copy('slave.py', 'tests' + os.path.sep + 'slave2')
        shutil.copy('slave.py', 'tests' + os.path.sep + 'slave3')
    except Exception:
        print("Erro ao realizar a cópia dos arquivos. Abortando...")
        stop_tests()

    print("Cópia realizada com sucesso")


def init_master_and_slaves():
    print("Iniciando processos slaves...")
    try:
        # Popen([executable, 'tests/slave1/slave.py'], shell=True)
        # Popen([executable, 'tests/slave2/slave.py'], shell=True)
        # Popen([executable, 'tests/slave3/slave.py'], shell=True)
        for i in range(3):
            spec = importlib.util.spec_from_file_location("slave.py", "tests/slave" + str(i + 1) + "/slave.py")
            slave = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(slave)
            server_thread = threading.Thread(target=slave.init_slave, args=())
            server_thread.daemon = True
            server_thread.start()
    except Exception as e:
        print("Um erro ocorreu. Abortando....: " + e.__str__())
        stop_tests()

    print("Iniciando processo master...")
    try:
        # Popen([executable, 'tests/master/master.py'], shell=True)
        from tests.master import master
        server_thread = threading.Thread(target=master.init_server, args=())
        server_thread.daemon = True
        server_thread.start()
    except Exception:
        print("Um erro ocorreu. Abortando....")
        stop_tests()


def init_tests():
    print('Iniciando os testes unitários')

    create_dirs()
    copy_py_files()
    copy_config_files()
    init_master_and_slaves()
    # delete_dirs()
    while (True):
        1 + 1


if __name__ == '__main__':
    init_tests()
