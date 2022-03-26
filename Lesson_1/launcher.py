""" Скрипт запуска/остановки скрипта сервера и клиентов """
import time
from subprocess import Popen, CREATE_NEW_CONSOLE

PROCESSED = []

while True:
    user = input('Запуск сервера и клиентов (s) / Закрытие клиентов (x) / '
                 'Выход (q):  ')

    if user == 'q':
        break

    elif user == 's':
        PROCESSED.append(Popen('python server.py',
                               creationflags=CREATE_NEW_CONSOLE))
        for i in range(3):
            time.sleep(0.5)
            PROCESSED.append(Popen(f'python client.py -n client{i + 1}',
                                   creationflags=CREATE_NEW_CONSOLE))
    elif user == 'x':
        while PROCESSED:
            _ = PROCESSED.pop()
            _.kill()
        PROCESSED.clear()
