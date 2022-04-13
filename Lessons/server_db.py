from sqlalchemy import create_engine, Table, Column, Integer, String, \
    MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from datetime import datetime

from common.variables import *


# Класс для серверной БД
class ServerDb:
    # класс для отображения всех пользователей приложения
    class AllUsers:
        def __init__(self, user_name):
            self.id = None
            self.user_name = user_name
            self.last_login = datetime.now()

    # класс для отображения всех активный пользователей приложения (real_time)
    class ActiveUsers:
        def __init__(self, user_id, addr, port, login_time):
            self.id = None
            self.user_id = user_id
            self.addr = addr
            self.port = port
            self.login_time = login_time

    # класс для отображения истории логирования пользователя в приложении
    class LoginHistory:
        def __init__(self, date, addr, port, login):
            self.id = None
            self.date = date
            self.addr = addr
            self.port = port
            self.login = login

    # класс для отображения списка контактов пользователя
    class UserContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    # класс для отображения истории действий пользователя
    class UserHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = int(0)
            self.accepted = int(0)

    def __init__(self, path):
        # создаём движок БД сервера
        print(path)
        self.db_engine = create_engine(f'sqlite:///{path}',
                                       echo=False,
                                       pool_recycle=3600,
                                       connect_args={
                                           'check_same_thread': False})
        # создаём объект MetaData
        self.meta_data = MetaData()

        # создание таблицы пользователей приложения
        users_table = Table('Users', self.meta_data,
                            Column('id', Integer, primary_key=True),
                            Column('user_name', String, unique=True),
                            Column('last_login', DateTime))

        # создание таблицы активных пользователей приложения
        active_user_table = Table('Active_users', self.meta_data,
                                  Column('id', Integer, primary_key=True),
                                  Column('user_id', ForeignKey('Users.id'),
                                         unique=True),
                                  Column('addr', String),
                                  Column('port', Integer),
                                  Column('login_time', DateTime))

        # создание таблицы логирования пользователей приложения
        login_history_table = Table('Login_history', self.meta_data,
                                    Column('id', Integer, primary_key=True),
                                    Column('date', DateTime),
                                    Column('addr', String),
                                    Column('port', Integer),
                                    Column('login', ForeignKey('Users.id')))

        # создание таблицы контактов пользователей приложения
        contacts_table = Table('Contacts', self.meta_data,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id')))

        # создание таблицы истории пользователей приложения
        users_history_table = Table('History', self.meta_data,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('Users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer))

        # создание таблиц в БД
        self.meta_data.create_all(self.db_engine)

        # создание привязки (отображения)
        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_user_table)
        mapper(self.LoginHistory, login_history_table)
        mapper(self.UserContacts, contacts_table)
        mapper(self.UserHistory, users_history_table)

        # инициируем сессию
        Session = sessionmaker(bind=self.db_engine)
        self.session = Session()

        # очищаем таблицу активных пользователей
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    # функция записи в БД факта входа пользователя, выполняется при входе
    def user_login(self, user_name, addr, port):
        # Запрос в БД на наличие пользователя с таким именем
        user_log = self.session.query(self.AllUsers).filter_by(
            user_name=user_name)

        # при нахождении обновляем дату и время последнего входа
        if user_log.count():
            user = user_log.first()
            user.last_login = datetime.now()
        # в случаи отсутствия, создаём нового пользователя
        else:
            user = self.AllUsers(user_name)
            self.session.add(user)
            # для присвоения ID нужен коммит
            self.session.commit()
            users_history = self.UserHistory(user.id)
            self.session.add(users_history)

        # создаем запись в таблице активных пользователей
        new_active_user = self.ActiveUsers(user.id, addr, port, datetime.now())
        self.session.add(new_active_user)

        # также сохраняем запись в таблице истории
        history = self.LoginHistory(datetime.now(), addr, port, user.id)
        self.session.add(history)

        self.session.commit()

    # функция фиксирующая отключение пользователя, для удаления из таблицы
    # активных пользователей
    def user_logout(self, user_name):

        user = self.session.query(self.AllUsers).filter_by(
            user_name=user_name).first()
        self.session.query(self.ActiveUsers).filter_by(
            user_id=user.id).delete()
        self.session.commit()

    # функция возвращает всех известных пользователей и время последнего
    # входа
    def users_list(self):
        query = self.session.query(
            self.AllUsers.user_name, self.AllUsers.last_login,)
        return query.all()  # список кортежей (логин, время)

    # функция возвращает список активных пользователей
    def active_users_list(self):
        query = self.session.query(
            self.AllUsers.user_name,
            self.ActiveUsers.addr,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        # отдаёт список кортежей (логин, адрес, порт, время)
        return query.all()

    # функция возвращает историю входов пользователей или конкретного юзера
    def login_history(self, user_name=None):

        query = self.session.query(
            self.AllUsers.name,
            self.LoginHistory.date,
            self.LoginHistory.addr,
            self.LoginHistory.port
        ).join(self.AllUsers)

        if user_name:
            query = query.filter(self.AllUsers.name == user_name)

        return query.all()

    # Функция фиксирует передачу сообщения и делает отметки в БД
    def process_message(self, sender, recipient):
        # Получаем ID отправителя и получателя
        sender = self.session.query(self.AllUsers).filter_by(
            user_name=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(
            user_name=recipient).first().id
        # Запрашиваем строки из истории и увеличиваем счётчики
        sender_row = self.session.query(self.UserHistory).filter_by(
            user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UserHistory).filter_by(
            user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    # функция добавления к контактам пользователя
    def add_contact(self, user, contact):

        user = self.session.query(self.AllUsers).filter_by(
            user_name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(
            user_name=contact).first()
        if not contact or self.session.query(self.UserContacts).filter_by(
            user=user.id, contact=contact.id).count():
            return

        contact_row = self.UserContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    # функция для удаления из списка контактов пользователя
    def remove_contact(self, user, contact):
        user = self.session.query(self.AllUsers).filter_by(
            user_name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(
            user_name=contact).first()
        # если контакта нет в списке контактов просто выходим из функции
        if not contact:
            return

        print(self.session.query(self.UserContacts).filter(
            self.UserContacts.user == user.id,
            self.UserContacts.contact == contact.id).delete())
        self.session.commit()

    # функция возвращает список контактов пользователя
    def get_contacts(self, user_name):
        user = self.session.query(self.AllUsers).filter_by(
            user_name=user_name).one()
        query = self.session.query(
            self.UserContacts, self.AllUsers.user_name).filter_by(
            user_name=user.id).join(
            self.AllUsers,
            self.UserContacts.contact == self.AllUsers.id)

        return [contact[1] for contact in query.all()]

    # функция возвращает количество полученных и отправленных сообщений
    def message_history(self):
        query = self.session.query(
            self.AllUsers.user_name,
            self.AllUsers.last_login,
            self.UserHistory.sent,
            self.UserHistory.accepted).join(self.AllUsers)
        return query.all()


if __name__ == '__main__':
    test_db = ServerDb()
    test_db.user_login('1111', '192.168.5.20', 8080)
    test_db.user_login('2222', '192.168.5.21', 8081)
    print(test_db.users_list())
    # print(test_db.active_users_list())
    # test_db.user_logout('McG')
    # print(test_db.login_history('re'))
    # test_db.add_contact('test2', 'test1')
    # test_db.add_contact('test1', 'test3')
    # test_db.add_contact('test1', 'test6')
    # test_db.remove_contact('test1', 'test3')
    test_db.process_message('McG2', '1111')
    print(test_db.message_history())
