from subprocess import Popen, CREATE_NEW_CONSOLE

process = []

while True:
    action = input('Выберите действие: q - выход , s - запустить сервер, c - '
                   'запустить клиенты x - закрыть все окна:')
    if action == 'q':
        print('Good bye!')
        break
    elif action == 's':
        # Запускаем сервер!
        process.append(Popen(
            'python server.py', creationflags=CREATE_NEW_CONSOLE, shell=True))
        print('Поступила команда на запуск сервера!')
    elif action == 'c':
        clients_count = int(input('Введите количество клиентов для запуска: '))
        # Запускаем клиентов:
        for i in range(clients_count):
            process.append(Popen(
                f'python client.py -n test{i + 1}',
                creationflags=CREATE_NEW_CONSOLE, shell=True))
        print(f'Поступила команда на запуск {clients_count} клиентов')
    elif action == 'x':
        while process:
            process.pop().kill()
