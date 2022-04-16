""" Скрипт запуска/остановки скрипта сервера и клиентов """
import time
from subprocess import Popen, CREATE_NEW_CONSOLE

processed = []

while True:
    user = input('Запуск сервера и клиентов (s) / Закрытие клиентов (x) / '
                 'Выход (q):  ')

    if user == 'q':
        break

    elif user == 's':
        clients_count = int(input('Введите количество клиентов для запуска: '))
        processed.append(Popen('python server.py',
                               creationflags=CREATE_NEW_CONSOLE, shell=True))
        for i in range(clients_count):
            time.sleep(0.5)
            processed.append(Popen(f'python client.py -n client{i + 1}',
                                   creationflags=CREATE_NEW_CONSOLE,
                                   shell=True))
    elif user == 'x':
        while processed:
            processed.pop().kill()
        processed.clear()
