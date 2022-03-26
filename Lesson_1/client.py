"""Программа клиента"""
import json
import sys
import time
import argparse
from threading import Thread
from log_decorator import log
from socket import socket, AF_INET, SOCK_STREAM
from common.variables import ACTION, ACCOUNT_NAME, DEFAULT_IP_ADDRESS, \
    DEFAULT_PORT, ERROR, MESSAGE, MESSAGE_TEXT, PRESENCE, RESPONSE, TIME, \
    USER, SENDER, EXIT, DESTINATION
from common.utils import read_message, send_message
from logs.client_log_config import client_logger as logger

logger.info('Клиент начинает работу!')


@log
def exit_message(account_name):
    # Функция создаёт сообщение о выходе
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account_name,
    }


@log
def server_answer(sock, my_username):
    """
    Обработчик сообщений с сервера
    :param message:
    :return:
    """
    while True:
        try:
            message = read_message(sock)
            if ACTION in message and message[ACTION] == MESSAGE and SENDER in\
                    message and MESSAGE_TEXT in message and DESTINATION in \
                    message and message[DESTINATION] == my_username:
                print(f'Получено сообщение от пользователя {message[SENDER]}:'
                      f'\n{message[MESSAGE_TEXT]}.')
                logger.info(f'Получено сообщение от пользователя '
                            f' {message[SENDER]}: {message[MESSAGE_TEXT]}')
            else:
                logger.error(f'Получено некорректное сообщение от сервера: '
                             f'{message}')
        except json.JSONDecodeError:
            logger.error('Не удалось декодировать сообщение.')
        except Exception:
            logger.critical('Потеряно соединение с сервером.')
            break


@log
def server_answer_response(message):
    """
    Функция разбора приветственного сообщения. 200 если все ОК, 400 при ошибке.
    :param message:
    :return:
    """
    logger.info(f'Разбор приветственного сообщения от сервера: {message}.')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200: OK'
        elif message[RESPONSE] == 400:
            raise f'400: {message[ERROR["Ошибка сервера"]]}'
    raise f'В принятом словаре отсутствует обязательное поле ' \
          f'{message[RESPONSE]}'


@log
def create_presence(account_name='Guest'):
    """
    Функция для отправки запроса о присутствии клиента
    :param account_name:
    :return:
    """
    presence_dict = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {ACCOUNT_NAME: account_name},
    }
    logger.info(f'Сформировано сообщение {PRESENCE}')

    return presence_dict


@log
def create_message(sock, account_name='Guest'):
    """
    функция создания словаря согласно требованиям JIM протокола, запрашиваает
    кому адресованно и сообщение, затем отправляет на сервер.
    :param sock: сокет подключения
    :param account_name: по умолчанию 'Guest'
    :return: dict
    """
    to_user = input('Введите получателя сообщения: ')
    message = input('Введите ваше сообщение (текст) и нажмите "Enter", для '
                    'выхода "exit". ')
    message_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        TIME: time.time(),
        DESTINATION: to_user,
        MESSAGE_TEXT: message,
    }
    logger.debug(f'Сформирован словарь сообщения: {message_dict}')
    try:
        send_message(sock, message_dict)
        logger.info(f'Отправленно сообщение для пользователя {to_user}.')
    except Exception as e:
        print(e)
        logger.critical('Потеряно соединение с сервером.')
        sys.exit(1)


def print_help():
    """Справка для пользователя"""
    print('\nСписок поддерживаемых команд: ')
    print('message - отправка сообщения. Будет запрошен адресат и сообщение.')
    print('help - вывод справки по командам.')
    print('exit - выход из программы.')


@log
def user_interactive(sock, username):
    """
    Функция запроса команд у пользователя
    :param sock:
    :param username:
    :return:
    """
    print_help()
    while True:
        command = input('Введите команду: ')
        if command.lower() == 'message':
            create_message(sock, username)
        elif command.lower() == 'exit':
            send_message(sock, exit_message(username))
            print('Закрытие соединения. Good bye!!!')
            logger.info('Клиент завершил работу приложения.')
            time.sleep(0.5)
            break
        elif command.lower() == 'help':
            print_help()
        else:
            print('Команда не распознана, попробуйте снова. help - для вызова'
                  ' справки.')


@log
def command_line_parser():
    """
    Парсер для чтения параметров запуска скрипта клиента
    :return: адрес, порт, режим работы клиента
    """
    logger.info('Запуск клиента... Анализ параметров запуска...')
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    args = parser.parse_args(sys.argv[1:])
    serv_addr = args.addr
    serv_port = args.port
    client_name = args.name

    if not 65636 > serv_port > 1023:
        logger.critical(f'Ошибка применения параментра порта {serv_port}, так'
                        f' как параметр не удовлетворяет требованиям.')
        print(f'Ошибка параментра порта {serv_port}, так как параметр не '
              f'удовлетворяет требованиям. Допустимо: от 1024 до 65635.')
        sys.exit(1)
    #
    # if client_mode not in ('listen', 'send'):
    #     logger.critical(f'Некорректно указан режим работы клиента'
    #                     f' {client_mode}, доступные режимы: listen, send.')
    #     sys.exit(1)
    return serv_addr, serv_port, client_name


def main():
    """
    Загрузка параметров из командной строки, в случаи отсутствия присваиваем
    параметры по умолчанию, из файла variables.py
    :return:
    """
    # проводим проверку полученных параметров запуска
    serv_address, serv_port, client_name = command_line_parser()
    if not client_name:
        client_name = input('Введите имя пользователя: ')

    logger.info(f'Клиент запущен: адрес сервера - {serv_address}, '
                f'порт - {serv_port}, имя пользователя - {client_name}.')

#     if len(sys.argv) == 1:
#         serv_address = DEFAULT_IP_ADDRESS
#         serv_port = DEFAULT_PORT
#         logger.info(f'Применены параметры запуска по умолчанию; адрес '
#                     f'сервера-{serv_address}, порт- {serv_port}.')
#     elif len(sys.argv) == 2:
#         serv_address = sys.argv[1]
#         serv_port = DEFAULT_PORT
#         logger.info(f'Применены параметры запуска; адрес сервера'
#                     f'-{serv_address}, порт по умолчанию- {serv_port}.')
#     elif len(sys.argv) == 3:
#         serv_address = sys.argv[1]
#         serv_port = int(sys.argv[2])
#         logger.info(f'Применены параметры запуска; адрес сервера-'
#                     f'{serv_address}, порт-{serv_port}.')
#     elif len(sys.argv) > 3:
#         logger.error(f'Получены избыточные параметры запуска '
#                      f'{sys.argv[3:]}')
# except IndexError:
#     serv_address = DEFAULT_IP_ADDRESS
#     serv_port = DEFAULT_PORT
#     logger.info(f'Применены параметры запуска по умолчанию; адрес сервера-'
#                 f'{serv_address}, порт-{serv_port}.')
# except ValueError:
#     logger.critical('Клиент не запущен. Произошла ошибка запуска которая '
#                     'вызвала остановку программы с кодом 1')
#     print('Можно указать два параметра через пробел:\n'
#           'Первый: ip-адрес сервера \n'
#           'Второй: tcp-порт на сервере\n'
#           'или указать только ip, хотя если лень можно и без параметров')
#     sys.exit(1)

    try:
        client_socket = socket(AF_INET, SOCK_STREAM)
        logger.debug(f'Создан клиентский сокет.')
        client_socket.connect((serv_address, serv_port))
        send_message(client_socket, create_presence(client_name))
        answer = server_answer_response(read_message(client_socket))
        logger.info(f'Установлено соединение. Ответ сервера: {answer}')
    except json.JSONDecodeError:
        logger.error(f'Не удалось декодировать полученную JSON строку.')
        sys.exit(1)
    except Exception as error:
        logger.error(f'При установке соединения сервер вернул ошибку: {error}')
        sys.exit(1)
    else:
        receiver = Thread(target=server_answer, args=(client_socket,
                                                      client_name))
        receiver.daemon = True
        receiver.start()

        user_interface = Thread(target=user_interactive, args=(client_socket,
                                                               client_name))
        user_interface.daemon = True
        user_interface.start()
        logger.debug('Процессы запущены.')

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break
        # if client_mode == 'listen':
        #     print('Режим работы: приём сообщений')
        # else:
        #     print('Режим работы: отправка сообщений')
        # while True:     # бесконечный цикл до ввода **** или закрытия консоли
        #     if client_mode == 'listen':
        #         try:
        #             server_answer(read_message(client_socket))
        #         except Exception as err:
        #             logger.warning(f'Соединение с сервером было потеряно. '
        #                            f'Ошибка: {err}')
        #             print('Соединение с сервером было потеряно.')
        #             sys.exit(1)
        #     if client_mode == 'send':
        #         try:
        #             send_message(client_socket, create_message(client_socket))
        #         except Exception as err:
        #             logger.warning(f'Соединение с сервером было потеряно. '
        #                            f'Ошибка: {err}')
        #             sys.exit(1)


if __name__ == '__main__':
    main()
