"""Программа клиента"""
import json
import sys
import time
import argparse
from threading import Thread

from Lessons.metaclass import ClientVerifier
from log_decorator import log
from socket import socket, AF_INET, SOCK_STREAM
from common.variables import ACTION, ACCOUNT_NAME, DEFAULT_IP_ADDRESS, \
    DEFAULT_PORT, ERROR, MESSAGE, MESSAGE_TEXT, PRESENCE, RESPONSE, TIME, \
    USER, SENDER, EXIT, DESTINATION
from common.utils import read_message, send_message
from logs.client_log_config import client_logger as logger

logger.info('Клиент начинает работу!')


# Класс формирования и отправки сообщения на сервер также отвечает за
# взаимодействие с пользователем.
class ClientSender(Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock

    @log
    def exit_message(self):
        # Функция создаёт сообщение о выходе
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name,
        }

    @log
    def create_message(self):
        """
        функция создания словаря согласно требованиям JIM протокола, запрашиваает
        кому адресованно и сообщение, затем отправляет на сервер.
        :param sock: сокет подключения
        :param account_name: по умолчанию 'Guest'
        :return: dict
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите ваше сообщение (текст) и нажмите "Enter", для'
                        'выхода "exit". ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            TIME: time.time(),
            DESTINATION: to_user,
            MESSAGE_TEXT: message,
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            logger.info(f'Отправленно сообщение для пользователя {to_user}.')
        except Exception as e:
            print(e)
            logger.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    @log
    def print_help(self):
        """Справка для пользователя"""
        print('\nСписок поддерживаемых команд: ')
        print('message - отправка сообщения. Будет запрошен адресат и '
              'сообщение.')
        print('help - вывод справки по командам.')
        print('exit - выход из программы.')

    @log
    def user_interactive(self):
        """
        Функция запроса команд у пользователя
        :param sock:
        :param username:
        :return:
        """
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command.lower() == 'message':
                self.create_message()
            elif command.lower() == 'exit':
                try:
                    send_message(self.sock, self.exit_message())
                except:
                    pass
                print('Закрытие соединения. Good bye!!!')
                logger.info('Клиент завершил работу приложения.')
                time.sleep(0.5)
                break
            elif command.lower() == 'help':
                self.print_help()
            else:
                print(
                    'Команда не распознана, попробуйте снова. help - для '
                    'вызова справки.')


# Класс клиента отвечающего за прием сообщения, печать сообщения и завершается
# при потере соединения с сервером.
class ClientReader(Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super.__init__()

    # Основной цикл класса
    @log
    def server_answer(self):
        """
        Обработчик сообщений с сервера
        :param message:
        :return:
        """
        while True:
            try:
                message = read_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and SENDER\
                        in message and MESSAGE_TEXT in message and DESTINATION\
                        in message and message[DESTINATION] == \
                        self.account_name:
                    print(f'Получено сообщение от пользователя '
                          f'{message[SENDER]}: \n{message[MESSAGE_TEXT]}.')
                    logger.info(f'Получено сообщение от пользователя '
                                f' {message[SENDER]}: {message[MESSAGE_TEXT]}')
                else:
                    logger.error(f'Получено некорректное сообщение от сервера:'
                                 f' {message}')
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
        receiver = ClientReader(client_name, client_socket)
        receiver.daemon = True
        receiver.start()

        sender_module = ClientSender(client_name, client_socket)
        sender_module.daemon = True
        sender_module.start()
        logger.debug('Процессы запущены.')

        while True:
            time.sleep(1)
            if receiver.is_alive() and sender_module.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
