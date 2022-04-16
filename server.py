# """
# Программа сервера
# """
# import configparser
# import os
# import sys
# import select
# import argparse
#
# import socket
# from threading import Thread, Lock
# from PyQt5.QtCore import QTimer
# from PyQt5.QtWidgets import QApplication, QMessageBox
#
# from server_gui import MainWindow, gui_create_model, HistoryWindow, \
#     create_stat_model, ConfigWindow
# from descriptor import PortDescriptor
# from metaclasses import ServerVerifier
# from common.variables import ACTION, ACCOUNT_NAME, MAX_CONNECTIONS, \
#     DESTINATION, PRESENCE, RESPONSE, TIME, USER, ERROR, MESSAGE, MESSAGE_TEXT, \
#     SENDER, EXIT, RESPONSE_200, GET_CONTACTS, RESPONSE_202, LIST_INFO, \
#     ADD_CONTACT, REMOVE_CONTACT, RESPONSE_400, USERS_REQUEST, DEFAULT_PORT, \
#     DEFAULT_IP_ADDRESS
# from common.utils import read_message, send_message
# from log_decorator import log
# from logs.server_log_config import server_logger
# from server_db import ServerDb
#
# # Флаг, что был подключён новый пользователь, нужен чтобы не мучать BD
# # постоянными запросами на обновление
# new_connection = False
# conflag_lock = Lock()
#
#
# @log
# def arg_parser(default_port, default_address):
#     """Парсер аргументов при запуске из командной строки."""
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-p', default=default_port, type=int, nargs='?')
#     parser.add_argument('-a', default=default_address, nargs='?')
#     namespace = parser.parse_args(sys.argv[1:])
#     listen_address = namespace.a
#     listen_port = namespace.p
#     return listen_address, listen_port
#
#
# class Server(Thread, metaclass=ServerVerifier):
#     # инициализация класса сервер
#     server_logger.info('Запуск сервера... Анализ параметров запуска...')
#     port = PortDescriptor()
#
#     def __init__(self, listen_address, listen_port, database):
#         # Параметры подключения
#         self.listen_address = listen_address
#         self.port = listen_port
#
#         self.database = database
#
#         # список подключенных клиентов
#         self.all_clients = []
#
#         # Список сообщений для отправки
#         self.messages = []
#
#         # Словарь соответствий имени и сокета клиента
#         self.names = dict()
#
#         # Конструктор предка
#         super().__init__()
#
#     def init_socket(self):
#         server_logger.info(f'Сервер запущен, порт для подключений: '
#                            f'{self.port}, адрес подключения: '
#                            f'{self.listen_address}. Если адрес не указан, '
#                            f'соединения принимаются с любых адресов.')
#         server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         server.bind((self.listen_address, self.port))
#         server.settimeout(0.5)
#
#         # Начинаем слушать сокет
#         self.sock = server
#         self.sock.listen()
#
#     def main_loop(self):
#         # Инициализация сокета
#         global new_connection
#         self.init_socket()
#
#         # Основной цикл программы сервера
#         while True:
#             try:  # Ждём подключения
#                 client_socket, client_address = self.sock.accept()
#                 server_logger.info(f'Установлено соединение с клиентом '
#                                    f'{client_address}.')
#             except OSError as err:  # Ловим исключения по таймауту
#                 # Номер ошибки None потому что ошибка по таймауту
#                 print(err.errno)
#                 pass
#             else:
#                 server_logger.info(
#                     f'Установлено соединение с {client_address}.')
#                 self.all_clients.append(client_socket)
#
#             recv_data_lst = []
#             send_data_lst = []
#             err_lst = []
#             # Проверяем на наличие ждущих клиентов
#             try:
#                 if self.all_clients:
#                     recv_data_lst, send_data_lst, err_lst = select.select(
#                         self.all_clients, self.all_clients, [], 0)
#             except OSError:
#                 pass
#
#             # Принимаем сообщение, если ошибка исключаем клиентский сокет
#             if recv_data_lst:
#                 for client_message in recv_data_lst:
#                     try:
#                         self.check_and_create_answer_to_client(
#                             read_message(client_message), client_message)
#                     except (OSError):
#                         # Ищем клиента в словаре клиентов и удаляем его
#                         server_logger.info(
#                             f'Клиент {client_message.getpeername()}'
#                             f'отключился от сервера.')
#                         self.all_clients.remove(client_message)
#                         for name in self.names:
#                             if self.names[name] == client_message:
#                                 self.database.user_logout(name)
#                                 del self.names[name]
#                                 break
#
#             # Если есть сообщения, обрабатываем каждое в цикле
#             for i in self.messages:
#                 try:
#                     self.process_message(i, send_data_lst)
#                 except:
#                     server_logger.info(f'Связь с клиентом {i[DESTINATION]} '
#                                        f'была потеряна.')
#                     self.all_clients.remove(self.names[i[DESTINATION]])
#                     self.database.user_logout(i[DESTINATION])
#                     del self.names[i[DESTINATION]]
#             self.messages.clear()
#
#     def process_message(self, message, listen_socket):
#         """
#             Функция доставки сообщения конкретному клиенту. Принимает словарь
#             сообщения, список пользователей и слушающие сокеты. Ничего не
#             возвращает.
#         """
#         if message[DESTINATION] in self.names and \
#                 self.names[message[DESTINATION]] in listen_socket:
#             send_message(self.names[message[DESTINATION]], message)
#             server_logger.info(f'Отправлено сообщение пользователю '
#                                f'{message[DESTINATION]} от пользователя'
#                                f' {message[SENDER]}.')
#         elif message[DESTINATION] in self.names and \
#                 self.names[message[DESTINATION]] not in listen_socket:
#             raise ConnectionError
#         else:
#             server_logger.error(
#                 f'Пользователь с логином {message[DESTINATION]}'
#                 f' не зарегистрирован на сервере. Сообщение не '
#                 f'отправленно.')
#
#     def check_and_create_answer_to_client(self, message, client):
#         """
#         Функция для проверки корректности сообщения от клиента, и создания
#         ответа
#         """
#         global new_connection
#         server_logger.info(f'Принято сообщение: {message}.')
#         # Если сообщение о присутствии
#         if ACTION in message and message[ACTION] == PRESENCE and TIME in\
#                 message and USER in message:
#             if message[USER][ACCOUNT_NAME] not in self.names.keys():
#                 self.names[message[USER][ACCOUNT_NAME]] = client
#                 client_ip, client_port = client.getpeername()
#                 self.database.user_login(message[USER][ACCOUNT_NAME],
#                                          client_ip, client_port)
#                 send_message(client, RESPONSE_200)
#                 with conflag_lock:
#                     new_connection = True
#             else:
#                 response = RESPONSE_400
#                 response[ERROR] = 'Такое имя уже зарегистрированно'
#                 send_message(client, response)
#                 self.all_clients.remove(client)
#                 client.close()
#             return
#         # Если сообщение, то добавляем в очередь сообщений.
#         # Ответ от сервера не нужен
#         elif ACTION in message and message[ACTION] == MESSAGE and TIME in \
#             message and MESSAGE_TEXT in message and SENDER in message and\
#             DESTINATION in message and self.names[message[SENDER]] == client:
#             self.messages.append(message)
#             self.database.process_message(message[SENDER], message[DESTINATION])
#             return
#         # Если клиент выходит
#         elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME\
#                 in message and self.names[message[ACCOUNT_NAME]] == client:
#             self.database.user_logout(message[ACCOUNT_NAME])
#             server_logger.info(f'Пользователь {message[ACCOUNT_NAME]} '
#                                f'отключился от сервера корректно.')
#             self.all_clients.remove(self.names[message[ACCOUNT_NAME]])
#             self.names[message[ACCOUNT_NAME]].close()
#             del self.names[message[ACCOUNT_NAME]]
#             with conflag_lock:
#                 new_connection = True
#             return
#         # запрос контакт-листа
#         elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in\
#                 message and self.names[message[USER]] == client:
#             response = RESPONSE_202
#             response[LIST_INFO] = self.database.get_contacts(message[USER])
#             send_message(client, response)
#         # добавление контакта
#         elif ACTION in message and message[ACTION] == ADD_CONTACT and \
#                 ACCOUNT_NAME in message and USER in message and \
#             self.names[message[USER]] == client:
#             self.database.add_contact(message[USER], message[ACCOUNT_NAME])
#             send_message(client, RESPONSE_200)
#         # удаление контакта
#         elif ACTION in message and message[ACTION] == REMOVE_CONTACT and \
#             ACCOUNT_NAME in message and USER in message and \
#             self.names[message[USER]] == client:
#             self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
#             send_message(client, RESPONSE_200)
#         # запрос известных пользователей
#         elif ACTION in message and message[ACTION] == USERS_REQUEST and \
#                 ACCOUNT_NAME in message \
#                 and self.names[message[ACCOUNT_NAME]] == client:
#             response = RESPONSE_202
#             response[LIST_INFO] = [user[0]
#                                    for user in self.database.users_list()]
#             send_message(client, response)
#         # Если сообщение не обработано отдаём Bad Request
#         else:
#             send_message(client, {
#                 RESPONSE: 400,
#                 ERROR: 'Получен некорректный запрос'
#             })
#             return
#
#
# def main():
#     # Загрузка файла конфигурации сервера
#     config = configparser.ConfigParser()
#
#     dir_path = os.path.dirname(os.path.realpath(__file__))
#     config.read(f"{dir_path}/{'server.ini'}")
#
#     # Загрузка параметров командной строки, если нет параметров, то задаём
#     # значения по умолчанию.
#     listen_address, listen_port = arg_parser(DEFAULT_PORT, DEFAULT_IP_ADDRESS)
#
#     # Инициализация базы данных
#     server_db = ServerDb(
#         os.path.join(
#             config['SETTINGS']['Database_path'],
#             config['SETTINGS']['Database_file']))
#
#     # создание экземпляра класса сервера.
#     server = Server(listen_address, listen_port, server_db)
#     server.daemon = True
#     server.start()
#
#     # Создаём графическое окуружение для сервера:
#     server_app = QApplication(sys.argv)
#     main_window = MainWindow()
#
#     # Инициализируем параметры в окна
#     main_window.statusBar().showMessage('Server Working')
#     main_window.active_clients_table.setModel(gui_create_model(server_db))
#     main_window.active_clients_table.resizeColumnsToContents()
#     main_window.active_clients_table.resizeRowsToContents()
#
#     # Функция обновляющая список подключённых, проверяет флаг подключения, и
#     # если надо обновляет список
#     def list_update():
#         global new_connection
#         if new_connection:
#             main_window.active_clients_table.setModel(
#                 gui_create_model(server_db))
#             main_window.active_clients_table.resizeColumnsToContents()
#             main_window.active_clients_table.resizeRowsToContents()
#             with conflag_lock:
#                 new_connection = False
#
#     # Функция создающяя окно со статистикой клиентов
#     def show_statistics():
#         global stat_window
#         stat_window = HistoryWindow()
#         stat_window.history_table.setModel(create_stat_model(server_db))
#         stat_window.history_table.resizeColumnsToContents()
#         stat_window.history_table.resizeRowsToContents()
#         stat_window.show()
#
#     # Функция создающяя окно с настройками сервера.
#     def server_config():
#         global config_window
#         # Создаём окно и заносим в него текущие параметры
#         config_window = ConfigWindow()
#         config_window.db_path.insert(config['SETTINGS']['Database_path'])
#         config_window.db_file.insert(config['SETTINGS']['Database_file'])
#         config_window.port.insert(config['SETTINGS']['Default_port'])
#         config_window.ip.insert(config['SETTINGS']['Listen_Address'])
#         config_window.save_btn.clicked.connect(save_server_config)
#
#     # Функция сохранения настроек
#     def save_server_config():
#         global config_window
#         message = QMessageBox()
#         config['SETTINGS']['Database_path'] = config_window.db_path.text()
#         config['SETTINGS']['Database_file'] = config_window.db_file.text()
#         try:
#             port = int(config_window.port.text())
#         except ValueError:
#             message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
#         else:
#             config['SETTINGS']['Listen_Address'] = config_window.ip.text()
#             if 1023 < port < 65536:
#                 config['SETTINGS']['Default_port'] = str(port)
#                 print(port)
#                 with open('server.ini', 'w') as conf:
#                     config.write(conf)
#                     message.information(
#                         config_window, 'OK', 'Настройки успешно сохранены!')
#             else:
#                 message.warning(
#                     config_window,
#                     'Ошибка',
#                     'Порт должен быть от 1024 до 65536')
#
#     # Таймер, обновляющий список клиентов 1 раз в секунду
#     timer = QTimer()
#     timer.timeout.connect(list_update)
#     timer.start(1000)
#
#     # Связываем кнопки с процедурами
#     main_window.refresh_button.triggered.connect(list_update)
#     main_window.show_history_button.triggered.connect(show_statistics)
#     main_window.config_btn.triggered.connect(server_config)
#
#     # Запускаем GUI
#     server_app.exec_()
#
#
# if __name__ == '__main__':
#     main()
import socket
import sys
import os
import argparse
import json
import logging
import select
import time
from threading import Thread, Lock
import configparser
from logs.server_log_config import server_logger as logger
from errors import IncorrectDataRecivedError
from common.variables import *
from common.utils import read_message, send_message
from log_decorator import log
from descriptor import PortDescriptor
from metaclasses import ServerVerifier
from server_db import ServerDb
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

# Инициализация логирования сервера.
# logger = logging.getLogger('server')

# Флаг, что был подключён новый пользователь, нужен чтобы не мучать BD
# постоянными запросами на обновление
new_connection = False
conflag_lock = Lock()


# Парсер аргументов коммандной строки.
@log
def arg_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


# Основной класс сервера
class Server(Thread, metaclass=ServerVerifier):
    port = PortDescriptor()

    def __init__(self, listen_address, listen_port, database):
        # Параментры подключения
        self.addr = listen_address
        self.port = listen_port

        # База данных сервера
        self.database = database

        # Список подключённых клиентов.
        self.clients = []

        # Список сообщений на отправку.
        self.messages = []

        # Словарь содержащий сопоставленные имена и соответствующие им сокеты.
        self.names = dict()

        # Конструктор предка
        super().__init__()

    def init_socket(self):
        logger.info(
            f'Запущен сервер, порт для подключений: {self.port} , адрес с которого принимаются подключения: {self.addr}. Если адрес не указан, принимаются соединения с любых адресов.')
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        # Начинаем слушать сокет.
        self.sock = transport
        self.sock.listen()

    def run(self):
        # Инициализация Сокета
        self.init_socket()

        # Основной цикл программы сервера
        while True:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с ПК {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Ошибка работы с сокетами: {err}')

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(
                            read_message(client_with_message), client_with_message)
                    except (OSError):
                        # Ищем клиента в словаре клиентов и удаляем его из него
                        # и  базы подключённых
                        logger.info(
                            f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)

            # Если есть сообщения, обрабатываем каждое.
            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    logger.info(
                        f'Связь с клиентом с именем {message[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[message[DESTINATION]])
                    self.database.user_logout(message[DESTINATION])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    # Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение, список зарегистрированых
    # пользователей и слушающие сокеты. Ничего не возвращает.
    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]
                                                             ] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            logger.info(
                f'Отправлено сообщение пользователю {message[DESTINATION]} от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, отправка сообщения невозможна.')

    # Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента, проверяет корректность, отправляет
    #     словарь-ответ в случае необходимости.
    def process_client_message(self, message, client):
        global new_connection
        logger.debug(f'Разбор сообщения от клиента : {message}')

        # Если это сообщение о присутствии, принимаем и отвечаем
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Если такой пользователь ещё не зарегистрирован, регистрируем,
            # иначе отправляем ответ и завершаем соединение.
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(
                    message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
                with conflag_lock:
                    new_connection = True
            else:
                response = RESPONSE_400
                response[ERROR] = 'Имя пользователя уже занято.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return

        # Если это сообщение, то добавляем его в очередь сообщений. Ответ не
        # требуется.
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message and self.names[message[SENDER]] == client:
            self.messages.append(message)
            self.database.process_message(
                message[SENDER], message[DESTINATION])
            return

        # Если клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            self.database.user_logout(message[ACCOUNT_NAME])
            logger.info(
                f'Клиент {message[ACCOUNT_NAME]} корректно отключился от сервера.')
            self.clients.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with conflag_lock:
                new_connection = True
            return

        # Если это запрос контакт-листа
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            send_message(client, response)

        # Если это добавление контакта
        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # Если это удаление контакта
        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)

        # Если это запрос известных пользователей
        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[LIST_INFO] = [user[0]
                                   for user in self.database.users_list()]
            send_message(client, response)

        # Иначе отдаём Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return


def main():
    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    # Загрузка параметров командной строки, если нет параметров, то задаём
    # значения по умоланию.
    listen_address, listen_port = arg_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    # Инициализация базы данных
    database = ServerDb(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    # Создание экземпляра класса - сервера и его запуск:
    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # Создаём графическое окуружение для сервера:
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализируем параметры в окна
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # Функция обновляющяя список подключённых, проверяет флаг подключения, и
    # если надо обновляет список
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # Функция создающяя окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()


if __name__ == '__main__':
    main()
