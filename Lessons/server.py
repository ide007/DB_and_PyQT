"""
Программа сервера
"""
import sys
import select
import argparse
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from common.variables import ACTION, ACCOUNT_NAME, MAX_CONNECTIONS, \
    DEFAULT_PORT, DEFAULT_IP_ADDRESS, DESTINATION, PRESENCE, RESPONSE, \
    TIME, USER, ERROR, MESSAGE, MESSAGE_TEXT, SENDER, EXIT
from common.utils import read_message, send_message
from log_decorator import log
from logs.server_log_config import server_logger


# @log
# def check_and_create_answer_to_client(message, messages_list, client, clients,
#                                       names):
#     """
#     Функция для проверки коректности сообщения от клиента, и создания ответа
#     :param message:
#     :param messages_list:
#     :param client:
#     :param clients:
#     :param names:
#     :return:
#     """
#     server_logger.info(f'Принято сообщение: {message}.')
#     # Если сообщение о присутсятвии
#     if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
#             and USER in message:
#         if message[USER][ACCOUNT_NAME] not in names.keys():
#             names[message[USER][ACCOUNT_NAME]] = client
#             send_message(client, {RESPONSE: 200})
#         else:
#             send_message(client, {RESPONSE: 400,
#                                   RESPONSE[ERROR]: 'Такое имя уже'
#                                                    ' зарегестрировано'
#                                   })
#             clients.remove(client)
#             client.close()
#         return
#     # server_logger.error(f'Сообщение {message} некорректно.')
#     # Если сообщение то добавляем в очередь сообщений.Ответ от сервера не нужен
#     elif ACTION in message and message[ACTION] == MESSAGE and TIME in message \
#             and MESSAGE_TEXT in message and SENDER in message and DESTINATION\
#             in message:
#         messages_list.append(message)
#         return
#     # Если клиент выходит
#     elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in \
#             message:
#         clients.remove(names[message[ACCOUNT_NAME]])
#         names[message[ACCOUNT_NAME]].close()
#         del names[message[ACCOUNT_NAME]]
#         return
#     # Если сообщение не обработано отдаём Bad Request
#     else:
#         send_message(client, {
#             RESPONSE: 400,
#             ERROR: 'Получен некорректный запрос'
#         })
#         return


# @log
# def process_message(message, names, listen_socket):
#     """
#     Функция доставки сообщения конкретному клиенту. Принимает словарь
#     сообщения, список пользователей и слушающие сокеты. Ничего не возвращает.
#     :param message:
#     :param names:
#     :param listen_socket:
#     :return:
#     """
#     if message[DESTINATION] in names and names[message[DESTINATION]] in\
#             listen_socket:
#         send_message(names[message[DESTINATION]], message)
#         server_logger.info(f'Отправлено сообщение пользователю '
#                            f'{message[DESTINATION]} от пользователя'
#                            f' {message[SENDER]}.')
#     elif message[DESTINATION] in names and names[message[DESTINATION]] not in \
#             listen_socket:
#         raise ConnectionError
#     else:
#         server_logger.error(f'Пользователь с логином {message[DESTINATION]}'
#                             f' не зарегистрирован на сервере. Сообщение не '
#                             f'отправлено.')


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


# @log
# def new_socket_listen(address):
#     sock = socket(AF_INET, SOCK_STREAM)
#     sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
#     sock.bind(address)
#     sock.settimeout(0.5)
#     return sock


class Server():
    # инициализация класса сервер
    server_logger.info('Запуск сервера... Анализ параметров запуска...')

    def __init__(self, listen_address, listen_port):
        # Параметры подключения
        self.listen_address = listen_address
        self.listen_port = listen_port

        # список подключенных клиентов
        self.all_clients = []

        # Список сообщений для отправки
        self.messages = []

        # Словарь соответствий имени и сокета клиента
        self.names = dict()

    def init_socket(self):
        server_logger.info(f'Сервер запущен, порт для подключений: '
                           f'{self.listen_port}, адрес подключения: '
                           f'{self.listen_address}.')
        server = socket(AF_INET, SOCK_STREAM)
        server.bind((self.listen_address, self.listen_port))
        server.settimeout(0.5)

        # Начинаем слушать сокет
        self.sock = server
        self.sock.listen()

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


# @log
# def main():
#     """
#     Загрузка параметров из командной строки, в случаи отсутствия присваиваем
#     параметры по умолчанию, из файла variables.py
#     """
#
#     listen_address, listen_port = arg_parser()
#     server_logger.info(f'Сервер запущен, порт для подключений: {listen_port},'
#                        f'адрес подключения: {listen_address}.')
#
#     #   создаем серверный сокет с заданными параметрами
#
#     server = (listen_address, listen_port)  # параметры сервера
#     sock = new_socket_listen(server)
#     sock.listen(MAX_CONNECTIONS)
#     all_clients = []  # список всех клиентов
#     messages = []  # список сообщений
#     names = dict()  # {client_name: client_socket}
#     # Основной цикл программы сервера
#     while True:
#         try:    # Ждём подключения
#             client_socket, client_address = sock.accept()
#             server_logger.info(f'Установлено соединение с клиентом '
#                                f'{client_address}.')
#         except OSError as err:  # Ловим исключения по таймауту
#             print(err.errno)  # Номер ошибки None потомучто ошибка по таймауту
#             pass
#         else:
#             server_logger.info(f'Установлено соединение с {client_address}.')
#             all_clients.append(client_socket)
#
#         recv_data_lst = []
#         send_data_lst = []
#         err_lst = []
#         # Проверяем на наличие ждущих клиентов
#         try:
#             if all_clients:
#                 recv_data_lst, send_data_lst, err_lst = select.select(
#                     all_clients, all_clients, [], 0
#                 )
#         except OSError:
#             pass
#
#         # Принимаем сообщение, если ошибка исключаем клиентский сокет
#         if recv_data_lst:
#             for client_message in recv_data_lst:
#                 try:
#                     check_and_create_answer_to_client(
#                         read_message(client_message),
#                         messages, client_message, all_clients, names)
#                 except Exception:
#                     server_logger.info(f'Клиент {client_message.getpeername()}'
#                                        f'отключился от сервера.')
#                     all_clients.remove(client_message)
#
#         # Если есть сообщения, обрабатывем каждое в цикле
#         for i in messages:
#             try:
#                 process_message(i, names, send_data_lst)
#             except Exception:
#                 server_logger.info(f'Связь с клиентом {i[DESTINATION]} '
#                                    f'была потеряна.')
#                 all_clients.remove(names[i[DESTINATION]])
#                 del names[i[DESTINATION]]
#             messages.clear()


def main():
    """
    Загрузка параметров из командной строки, в случаи отсутствия присваиваем
    параметры по умолчанию, из файла variables.py
    """
    listen_address, listen_port = arg_parser()

    # создание экземпляра класса сервера.
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
