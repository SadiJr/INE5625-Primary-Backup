import os


def run_tests():
    print("Iniciando testes")

    print("Testando upload...")
    os.system('python client.py -u files' + os.path.sep + 't1.txt -s')
    os.system('python client.py -u files' + os.path.sep + 't2.txt -s')

    print("Testando update...")

    for i in os.listdir('files'):
        f = open(i, 'wb')
        f.write(b'Adicionando mais linhas para update')
        f.close()

    os.system('python client.py -u files' + os.path.sep + 't1.txt -s')

    print('Testando delete...')

    os.system('python client.py -d t1.txt -s')
    os.system('python client.py -d t2.txt -s')


if __name__ == '__main__':
    run_tests()