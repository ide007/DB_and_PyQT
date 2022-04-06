"""
Программа сервера
"""
import sys
import select
import argparse
from socket import socket, AF_INET, SOCK_STREAM

from descriptor import PortDescriptor
from metaclass import ServerVerifier
from common.variables import ACTION, ACCOUNT_NAME, MAX_CONNECTIONS, \
    DEFAULT_PORT, DEFAULT_IP_ADDRESS, DESTINATION, PRESENCE, RESPONSE, \
    TIME, USER, ERROR, MESSAGE, MESSAGE_TEXT, SENDER, EXIT
from common.utils import read_message, send_message
from log_decorator import log
from logs.server_log_config import server_logger
from server_db import ServerDb


@log
def arg_parser():
    """Парсер аргументов при запуске из командной строки."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default=DEFAULT_IP_ADDRESS, nargs='?')
    args = parser.parse_args(sys.argv[1:])
    listen_port = args.p
    listen_address = args.a
    # Проверка на получение корректного номера порта для работы сервера
    if 65535 < listen_port < 1024:
        server_logger.warning(f'Ошибка применения параметра порта'
                              f' {listen_port}, так как параметр не'
                              f' удовлетворяющий требованиям. Допустимы порт'
                              f' в интервале от 1024 до 65535.')
        sys.exit(1)
    return listen_address, listen_port


class Server(metaclass=ServerVerifier):
    # инициализация класса сервер
    server_logger.info('Запуск сервера... Анализ параметров запуска...')
    port = PortDescriptor()

    def __init__(self, listen_address, listen_port, database):
        # Параметры подключения
        self.listen_address = listen_address
        self.port = listen_port

        self.database = database

        # список подключенных клиентов
        self.all_clients = []

        # Список сообщений для отправки
        self.messages = []

        # Словарь соответствий имени и сокета клиента
        self.names = dict()

    def init_socket(self):
        server_logger.info(f'Сервер запущен, порт для подключений: '
                           f'{self.port}, адрес подключения: '
                           f'{self.listen_address}.')
        server = socket(AF_INET, SOCK_STREAM)
        server.bind((self.listen_address, self.port))
        server.settimeout(0.5)

        # Начинаем слушать сокет
        self.sock = server
        self.sock.listen(MAX_CONNECTIONS)

    def main_loop(self):
        # Инициализация сокета
        self.init_socket()

        # Основной цикл программы сервера
        while True:
            try:  # Ждём подключения
                client_socket, client_address = self.sock.accept()
                server_logger.info(f'Установлено соединение с клиентом '
                                   f'{client_address}.')
            except OSError as err:  # Ловим исключения по таймауту
                # Номер ошибки None потому что ошибка по таймауту
                print(err.errno)
                pass
            else:
                server_logger.info(
                    f'Установлено соединение с {client_address}.')
                self.all_clients.append(client_socket)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                if self.all_clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(
                        self.all_clients, self.all_clients, [], 0)
            except OSError:
                pass

            # Принимаем сообщение, если ошибка исключаем клиентский сокет
            if recv_data_lst:
                for client_message in recv_data_lst:
                    try:
                        self.check_and_create_answer_to_client(
                            read_message(client_message), client_message)
                    except:
                        server_logger.info(
                            f'Клиент {client_message.getpeername()}'
                            f'отключился от сервера.')
                        self.all_clients.remove(client_message)

            # Если есть сообщения, обрабатываем каждое в цикле
            for i in self.messages:
                try:
                    self.process_message(i, send_data_lst)
                except:
                    server_logger.info(f'Связь с клиентом {i[DESTINATION]} '
                                       f'была потеряна.')
                    self.all_clients.remove(self.names[i[DESTINATION]])
                    del self.names[i[DESTINATION]]
                self.messages.clear()

    def process_message(self, message, listen_socket):
        """
            Функция доставки сообщения конкретному клиенту. Принимает словарь
            сообщения, список пользователей и слушающие сокеты. Ничего не
            возвращает.
        """
        if message[DESTINATION] in self.names and \
                self.names[message[DESTINATION]] in listen_socket:
            send_message(self.names[message[DESTINATION]], message)
            server_logger.info(f'Отправлено сообщение пользователю '
                               f'{message[DESTINATION]} от пользователя'
                               f' {message[SENDER]}.')
        elif message[DESTINATION] in self.names and \
                self.names[message[DESTINATION]] not in listen_socket:
            raise ConnectionError
        else:
            server_logger.error(
                f'Пользователь с логином {message[DESTINATION]}'
                f' не зарегистрирован на сервере. Сообщение не '
                f'отправленно.')

    def check_and_create_answer_to_client(self, message, client):
        """
        Функция для проверки корректности сообщения от клиента, и создания
        ответа
        """
        server_logger.info(f'Принято сообщение: {message}.')
        # Если сообщение о присутствии
        if ACTION in message and message[ACTION] == PRESENCE and TIME in\
                message and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME],
                                         client_ip, client_port)
                send_message(client, {RESPONSE: 200})
            else:
                send_message(client, {RESPONSE: 400,
                                      RESPONSE[ERROR]: 'Такое имя уже'
                                                       ' зарегестрированно'
                                      })
                self.all_clients.remove(client)
                client.close()
            return
        # Если сообщение, то добавляем в очередь сообщений.
        # Ответ от сервера не нужен
        elif ACTION in message and message[ACTION] == MESSAGE and TIME in\
                message and MESSAGE_TEXT in message and SENDER in message and\
                DESTINATION in message:
            self.messages.append(message)
            return
        # Если клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME\
                in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.all_clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        # Если сообщение не обработано отдаём Bad Request
        else:
            send_message(client, {
                RESPONSE: 400,
                ERROR: 'Получен некорректный запрос'
            })
            return


def main():
    """
    Загрузка параметров из командной строки, в случаи отсутствия присваиваем
    параметры по умолчанию, из файла variables.py
    """
    listen_address, listen_port = arg_parser()

    server_db = ServerDb()

    # создание экземпляра класса сервера.
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
