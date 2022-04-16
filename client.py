"""Программа клиента"""
import json
import sys
import time
import argparse
from json import JSONDecodeError
from threading import Thread, Lock

from client_db import ClientDatabase
from errors import ServerError, IncorrectDataRecivedError, \
    ReqFieldMissingError
from metaclasses import ClientVerifier
from log_decorator import log
import socket
from common.variables import ACTION, ACCOUNT_NAME, DEFAULT_IP_ADDRESS, \
    DEFAULT_PORT, ERROR, MESSAGE, MESSAGE_TEXT, PRESENCE, RESPONSE, TIME, \
    USER, SENDER, EXIT, DESTINATION, ADD_CONTACT, GET_CONTACTS, LIST_INFO, \
    USERS_REQUEST, REMOVE_CONTACT
from common.utils import read_message, send_message
from logs.client_log_config import client_logger as logger

logger.info('Клиент начинает работу!')
sock_lock = Lock()
database_lock = Lock()


# Класс формирования и отправки сообщения на сервер также отвечает за
# взаимодействие с пользователем.
class ClientSender(Thread, metaclass=ClientVerifier):
    def __init__(self, login, sock, database):
        self.login = login
        self.sock = sock
        self.database = database
        super().__init__()

    # Функция для создания сообщения о корректном выходе
    @log
    def exit_message(self):
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.login,
        }

    # функция создания словаря согласно требованиям JIM протокола,
    # запрашивает кому адресовано сообщение, и затем отправляет на сервер.
    @log
    def create_message(self):

        to_user = input('Введите получателя сообщения:  ')
        message = input('Введите ваше сообщение (текст) и нажмите "Enter": ')

        # Проверка на наличие получателя
        with database_lock:
            if not self.database.check_user(to_user):
                logger.error(f'Попытка отправить сообщение '
                             f'незарегистрированому пользователю: {to_user}')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.login,
            TIME: time.time(),
            DESTINATION: to_user,
            MESSAGE_TEXT: message,
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        with database_lock:
            self.database.save_message(self.login, to_user, message)

        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                logger.info(f'Отправлено сообщение для пользователя '
                            f'{to_user}.')
            except OSError as e:
                if e.errno:
                    logger.critical('Потеряно соединение с сервером.')
                    sys.exit(1)
                else:
                    logger.error('Сообщение не доставлено. Таймаут соединения')

    @log
    def print_help(self):
        """Справка для пользователя"""
        print('\nСписок поддерживаемых команд: ')
        print('message - отправка сообщения. Будет запрошен адресат и '
              'сообщение.')
        print('help - вывод справки по командам.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('exit - выход из программы.')

    # Функция запроса команд у пользователя
    @log
    def user_interactive(self):

        self.print_help()

        while True:
            command = input('Введите команду: ')
            if command.lower() == 'message':
                self.create_message()
            elif command.lower() == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.exit_message())
                    except:
                        pass
                    print('Закрытие соединения. Good bye!!!')
                    logger.info('Клиент корректно завершил работу приложения.')
                time.sleep(0.5)
                break
            elif command.lower() == 'help':
                self.print_help()
            elif command.lower() == 'history':
                self.print_history()
            elif command.lower() == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for user in contacts_list:
                    print(user)
            elif command.lower() == 'edit':
                self.edit_contacts()
            else:
                print(
                    'Команда не распознана, попробуйте снова. help - для '
                    'вызова справки.')

    # Функция вывода истории
    def print_history(self):
        print('\nСписок поддерживаемых команд: ')
        print('in - входящие сообщения.')
        print('out - исходящие сообщения.')
        print('Для вывода всех сообщений нажмите - "Enter"  ')
        command = input('Введите команду:  ')

        with database_lock:
            if command.lower() == 'in':
                history = self.database.get_history(to_who=self.login)
                for message in history:
                    print(f'\nСообщение от пользователя: {message[0]} от '
                          f'{message[3]}:\n{message[2]}')
            elif command.lower() == 'out':
                history = self.database.get_history(from_who=self.login)
                for message in history:
                    print(f'\nСообщение пользователю: {message[1]} от '
                          f'{message[3]}:\n{message[2]}')
            elif command:
                history = self.database.get_history()
                for message in history:
                    print(f'\nСообщение от пользователя: {message[0]} '
                          f'пользователю: {message[1]} от {message[3]}:'
                          f'\n{message[2]}')
            else:
                print('Команда не распознана.')

    # Функция изменения контактов
    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемого контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error(
                        'Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.login, edit)
                    except ServerError:
                        logger.error(
                            'Не удалось отправить информацию на сервер.')


# Класс клиента отвечающего за прием сообщения, печать сообщения и завершается
# при потере соединения с сервером. Также сохраняет в данные в БД.
class ClientReader(Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    # Основной цикл класса
    @log
    def client_reader_run(self):
        while True:
            time.sleep(0.5)
            with sock_lock:

                try:
                    message = read_message(self.sock)
                except IncorrectDataRecivedError:
                    logger.error('Не удалось декодировать сообщение.')
                except OSError as err:
                    logger.error(f'Потеряно соединение с сервером. Код ошибки'
                                 f'{err.errno}.')
                    break
                except (ConnectionRefusedError, ConnectionError,
                        ConnectionResetError):
                    logger.error('Потеряно соединение с сервером.')
                    break
                except JSONDecodeError:
                    logger.error('Не удалось декодировать сообщение.')
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and \
                            SENDER in message and MESSAGE_TEXT in message and \
                            DESTINATION in message and message[DESTINATION] == \
                            self.account_name:
                        print(f'Получено сообщение от пользователя '
                              f'{message[SENDER]}: \n{message[MESSAGE_TEXT]}.')
                        with database_lock:
                            try:
                                self.database.save_message(
                                    message[SENDER],
                                    self.account_name,
                                    message[MESSAGE_TEXT])
                            except:
                                logger.critical('Ошибка взаимодействия с базой'
                                                ' данных.')
                        logger.info(f'Получено сообщение от пользователя '
                                    f' {message[SENDER]}: {message[MESSAGE_TEXT]}')
                    else:
                        logger.error(f'Получено некорректное сообщение от'
                                     f' сервера: {message}')


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
            raise ServerError(f'400: {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


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
    namespace = parser.parse_args(sys.argv[1:])
    serv_addr = namespace.addr
    serv_port = namespace.port
    client_name = namespace.name

    if not 65636 > serv_port > 1023:
        logger.critical(f'Ошибка применения параметра порта {serv_port}, так'
                        f' как параметр не удовлетворяет требованиям. '
                        f'Допустимо: от 1024 до 65635.')
        print(f'Ошибка параметра порта {serv_port}, так как параметр не '
              f'удовлетворяет требованиям. Допустимо: от 1024 до 65635.')
        sys.exit(1)

    return serv_addr, serv_port, client_name


# Функция добавления пользователя в контакт лист
def add_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = read_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


# Функция запрос контакт листа
def contacts_list_request(sock, name):
    logger.debug(f'Запрос контакт листа для пользователя {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        USER: name
    }
    logger.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = read_message(sock)
    logger.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


# Функция запроса списка известных пользователей
def user_list_request(sock, username):
    logger.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = read_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[LIST_INFO]
    else:
        raise ServerError


# Функция удаления пользователя из списка контактов
def remove_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = read_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удаление пользователя из списка контактов прошло успешно.')


# Функция инициализатор базы данных. Запускается при запуске, загружает
# данные в базу с сервера.
def database_load(sock, database, login):
    """
    Загружаем список зарегистрированных пользователей
    """
    try:
        users_list = user_list_request(sock, login)
    except ServerError:
        logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    # Загружаем список контактов
    try:
        contacts_list = contacts_list_request(sock, login)
    except ServerError:
        logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    """
    Загрузка параметров из командной строки, в случаи отсутствия присваиваем
    параметры по умолчанию, из файла variables.py
    :return:
    """
    # Сообщаем о запуске
    print('Консольный мессенджер. Клиентский модуль.')

    # проводим проверку полученных параметров запуска
    serv_address, serv_port, client_name = command_line_parser()
    # запрашиваем логин если он отсутствует в параметрах запуска
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен, ваш логин: {client_name}')

    logger.info(f'Клиент запущен: адрес сервера - {serv_address}, '
                f'порт - {serv_port}, имя пользователя - {client_name}.')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.settimeout(1)
        transport.connect((serv_address, serv_port))
        send_message(transport, create_presence(client_name))
        answer = server_answer_response(read_message(transport))
        logger.info(f'Установлено соединение. Ответ сервера: {answer}')
    except json.JSONDecodeError:
        logger.error(f'Не удалось декодировать полученную JSON строку.')
        sys.exit(1)
    except ServerError as err:
        print(f'При установке соединения сервер вернул ошибку:'
                     f' {err.text}')
        logger.error(f'При установке соединения сервер вернул ошибку:'
                     f' {err.text}')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        print(
            f'В ответе сервера отсутствует необходимое поле '
            f'{missing_error.missing_field}')
        logger.error(
            f'В ответе сервера отсутствует необходимое поле '
            f'{missing_error.missing_field}')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        print(f'Не удалось подключиться к серверу {serv_address}:'
              f'{serv_port}, конечный компьютер отверг запрос на '
              f'подключение.')
        logger.critical(
            f'Не удалось подключиться к серверу {serv_address}:{serv_port},'
            f'конечный компьютер отверг запрос на подключение.')
        exit(1)
    else:
        database = ClientDatabase(client_name)
        database_load(transport, database, client_name)

        receiver_module = ClientReader(client_name, transport, database)
        receiver_module.daemon = True
        receiver_module.start()

        sender_module = ClientSender(client_name, transport, database)
        sender_module.daemon = True
        sender_module.start()
        logger.debug('Процессы запущены.')

        while True:
            time.sleep(1)
            if receiver_module.is_alive() and sender_module.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
