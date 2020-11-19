import sys
import os
import shutil
from sys import executable
from subprocess import Popen


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
        sys.exit(0)

    print("Diretório do master criado com sucesso!")

    print("Criando diretórios dos slaves...")

    try:
        os.mkdir('tests' + os.path.sep + 'slave1')
        os.mkdir('tests' + os.path.sep + 'slave2')
        os.mkdir('tests' + os.path.sep + 'slave3')
    except OSError:
        print("Erro ao criar os diretórios dos slaves")
        sys.exit(0)


def copy_config_files():
    print("Copiando arquivos de configuração")
    try:
        shutil.copy('ips.conf', 'tests')
        shutil.copy('ips.conf', 'tests' + os.path.sep + 'master')
        shutil.copy('slave1.conf', 'tests' + os.path.sep + 'slave1')
        shutil.copy('slave2.conf', 'tests' + os.path.sep + 'slave2')
        shutil.copy('slave3.conf', 'tests' + os.path.sep + 'slave3')
    except OSError:
        print("Erro ao realizar a cópia dos arquivos de configuração. Abortando...")
        sys.exit()
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
        sys.exit(0)

    print("Cópia realizada com sucesso")


def init_master_and_slaves():
    print("Iniciando processo master...")
    try:
        Popen([executable, 'tests/master/master.py'], shell=True)
    except Exception:
        print("Um erro ocorreu. Abortando....")
        sys.exit()

    print("Iniciando processos slaves...")
    try:
        Popen([executable, 'tests/slave1/slave.py'], shell=True)
        Popen([executable, 'tests/slave2/slave.py'], shell=True)
        Popen([executable, 'tests/slave3/slave.py'], shell=True)
    except Exception:
        print("Um erro ocorreu. Abortando....")
        sys.exit(0)


def init_tests():
    print('Iniciando os testes unitários')

    create_dirs()
    copy_py_files()
    copy_config_files()
    init_master_and_slaves()
    delete_dirs()


if __name__ == '__main__':
    init_tests()