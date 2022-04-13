"""Программа клиента"""
import json
import sys
import time
import argparse
from threading import Thread, Lock

from metaclass import ClientVerifier
from log_decorator import log
from socket import socket, AF_INET, SOCK_STREAM
from common.variables import ACTION, ACCOUNT_NAME, DEFAULT_IP_ADDRESS, \
    DEFAULT_PORT, ERROR, MESSAGE, MESSAGE_TEXT, PRESENCE, RESPONSE, TIME, \
    USER, SENDER, EXIT, DESTINATION, GET_CONTACTS, LIST_INFO, ADD_CONTACT, \
    REMOVE_CONTACT
from common.utils import read_message, send_message
from logs.client_log_config import client_logger as logger
from client_db import ClientDatabase

logger.info('Клиент начинает работу!')

sock_lock = Lock()
database_lock = Lock()


# Класс формирования и отправки сообщения на сервер также отвечает за
# взаимодействие с пользователем.
class ClientSender(Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

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
        Функция создания словаря согласно JIM протокола, запрашивает
        кому адресовано и сообщение, затем отправляет на сервер.
        :return: dict
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите ваше сообщение (текст) и нажмите "Enter", для'
                        'выхода "exit". ')
        with database_lock:
            if not self.database.check_user(to_user):
                logger.error(f'Попытка отправки сообщения '
                             f'незарегистрированному пользователю: {to_user}')
                return

        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            TIME: time.time(),
            DESTINATION: to_user,
            MESSAGE_TEXT: message,
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        with database_lock:
            self.database.save_message(self.account_name, to_user, message)

        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                logger.info(f'Отправлено сообщение для пользователя {to_user}')
            except OSError as err:
                if err.errno:
                    logger.critical('Потеряно соединение с сервером.')
                    exit(1)
                else:
                    logger.error('Не удалось передать сообщение. '
                                 'Таймаут соединения.')

    @log
    def print_help(self):
        """Справка для пользователя"""
        print('\nСписок поддерживаемых команд: ')
        print('message - отправка сообщения. Будет запрошен адресат и '
              'сообщение.')
        print('history - история сообщений.')
        print('contacts - список контактов.')
        print('edit - редактирование списка контактов.')
        print('help - вывод справки по командам.')
        print('exit - выход из программы.')

    # функция вывода истории сообщений
    def print_history(self):
        command = input('in - показ входящих сообщений, out - исходящие,'
                        ' просто Enter: ')
        with database_lock:
            if command == 'in':
                history_list = self.database.get_history(
                    to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от '
                          f'{message[3]}:\n{message[2]}.')
            elif command == 'out':
                history_list = self.database.get_history(
                    from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от '
                          f'{message[3]}:\n{message[2]}.')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, '
                          f'пользователю {message[1]} от '
                          f'{message[3]}\n{message[2]}')

    @log
    def edit_contacts(self):
        command = input('Для удаления введите del, для добавления add: ')
        if command == 'del':
            edit = input('Введите имя удаляемого контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif command == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except Exception:
                        logger.error(
                            'Не удалось отправить информацию на сервер.')

    @log
    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            # Если отправка сообщения - соответствующий метод
            if command == 'message':
                self.create_message()

            # Вывод помощи
            elif command == 'help':
                self.print_help()

            # Выход. Отправляем сообщение серверу о выходе.
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_message(self.sock, self.exit_message())
                    except Exception:
                        pass
                    print('Завершение соединения.')
                    logger.info('Завершение работы по команде пользователя.')
                # Задержка необходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break

            # Список контактов
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            # Редактирование контактов
            elif command == 'edit':
                self.edit_contacts()

            # история сообщений.
            elif command == 'history':
                self.print_history()

            else:
                print('Команда не распознана, попробуйте снова. help - вывести'
                      ' поддерживаемые команды.')


# Класс клиента отвечающего за прием сообщения, печать сообщения и завершается
# при потере соединения с сервером.
class ClientReader(Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    # Основной цикл класса
    @log
    def run(self):
        """
        Обработчик сообщений с сервера
        """
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = read_message(self.sock)
                except json.JSONDecodeError:
                    logger.error('Не удалось декодировать сообщение.')
                except Exception:
                    logger.critical('Потеряно соединение с сервером.')
                    break
                else:
                    if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and MESSAGE_TEXT in message and \
                        DESTINATION in message and message[DESTINATION] \
                            == self.account_name:
                        print(f'Получено сообщение от пользователя '
                              f'{message[SENDER]}: \n{message[MESSAGE_TEXT]}.')
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER],
                                                           self.account_name,
                                                           message[
                                                               MESSAGE_TEXT])
                            except Exception:
                                logger.error('Ошибка взаимодействия с базой'
                                             ' данных')
                        logger.info(f'Получено сообщение от {message[SENDER]}:'
                                    f'\n{message[MESSAGE_TEXT]}')
                    else:
                        logger.error(f'Получено некорректное сообщение от '
                                     f'сервера: {message}')


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
    logger.info(f'Сформировано сообщение {PRESENCE} для пользователя '
                f'{account_name}')

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
        raise 'Ошибка создания контакта'
    print('Удачное создание контакта.')


# Функция запроса списка известных пользователей
@log
def contacts_list_request(sock, name):
    logger.debug(f'Запрос контакт листа для пользователся {name}')
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
        raise f'Получено некорректное сообщение от сервера'


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
        raise 'Ошибка удаления клиента'
    print('Удачное удаление')


# Функция инициализатор БД. Запускается при запуске, загружает данные с сервера
def database_load(sock, database, username):
    # Загружаем список известных пользователей
    try:
        users_list = contacts_list_request(sock, username)
    except Exception:
        logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    # Загружаем список контактов
    try:
        contacts_list = contacts_list_request(sock, username)
    except Exception:
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
    print('Консольный месседжер. Клиентский модуль.')
    # проводим проверку полученных параметров запуска
    serv_address, serv_port, client_name = command_line_parser()
    if not client_name:
        client_name = input('Введите имя пользователя: ')

    logger.info(f'Клиент запущен: адрес сервера - {serv_address}, '
                f'порт - {serv_port}, имя пользователя - {client_name}.')

    try:
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.settimeout(1)

        logger.debug(f'Создан клиентский сокет.')
        client_socket.connect((serv_address, serv_port))
        send_message(client_socket, create_presence(client_name))
        answer = server_answer_response(read_message(client_socket))
        logger.info(f'Установлено соединение. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        logger.error(f'Не удалось декодировать полученную JSON строку.')
        sys.exit(1)
    except Exception as error:
        logger.error(f'При установке соединения сервер вернул ошибку:'
                     f' {error}')
        sys.exit(1)
    else:
        database = ClientDatabase(client_name)
        database_load(client_socket, database, client_name)

        sender_module = ClientSender(client_name, client_socket, database)
        sender_module.daemon = True
        sender_module.start()
        logger.debug('Процессы запущены.')

        receiver = ClientReader(client_name, client_socket, database)
        receiver.daemon = True
        receiver.start()
        while True:
            time.sleep(1)
            if receiver.is_alive() and sender_module.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
