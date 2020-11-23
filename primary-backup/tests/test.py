import os

print("Iniciando testes")

print("Testando upload...")
os.system('python front_end.py -u files' + os.path.sep + 't1.txt -s')
os.system('python front_end.py -u files' + os.path.sep + 't2.txt -s')

print("Testando update...")
#Atualizar arquivos aqui

for i in os.listdir('tests'):
    f = open(i, 'wb')
    f.write(b'Adicionando mais linhas para update')
    f.close()

print('Testando delete...')
#Idem

