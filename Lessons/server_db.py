import username as username
from sqlalchemy import create_engine, Table, Column, Integer, String, \
    MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from datetime import datetime

from common.variables import ACTION, ACCOUNT_NAME, MAX_CONNECTIONS, \
    DEFAULT_PORT, DEFAULT_IP_ADDRESS, DESTINATION, PRESENCE, RESPONSE, \
    TIME, USER, ERROR, MESSAGE, MESSAGE_TEXT, SENDER, EXIT, SERVER_DATABASE


class ServerDb:
    class AllUsers:
        def __init__(self, user_name):
            self.id = None
            self.user_name = user_name
            self.last_login = datetime.now()

    class ActiveUsers:
        def __init__(self, user_id, addr, port, login_time):
            self.id = None
            self.user_id = user_id
            self.addr = addr
            self.port = port
            self.login_time = login_time

    class LoginHistory:
        def __init__(self, date, addr, port, login):
            self.id = None
            self.date = date
            self.addr = addr
            self.port = port
            self.login = login

    def __init__(self):
        self.db_engine = create_engine(SERVER_DATABASE, echo=False,
                                       pool_recycle = 3600)
        self.meta_data = MetaData()
        users_table = Table('Users', self.meta_data,
                            Column('id', Integer, primary_key=True),
                            Column('user_name', String, unique=True),
                            Column('last_login', DateTime))

        active_user_table = Table('Active_users', self.meta_data,
                                  Column('id', Integer, primary_key=True),
                                  Column('user_id', ForeignKey('Users.id'),
                                         unique=True),
                                  Column('addr', String),
                                  Column('port', Integer),
                                  Column('login_time', DateTime))

        login_history_table = Table('Login_history', self.meta_data,
                                    Column('id', Integer, primary_key=True),
                                    Column('date', DateTime),
                                    Column('addr', String),
                                    Column('port', Integer),
                                    Column('login', ForeignKey('Users.id')))

        self.meta_data.create_all(self.db_engine)

        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_user_table)
        mapper(self.LoginHistory, login_history_table)

        Session = sessionmaker(bind=self.db_engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, user_name, addr, port):

        user_log = self.session.query(self.AllUsers).filter_by(
            user_name=user_name)

        if user_log.count():
            user = user_log.first()
            user.last_login = datetime.now()
        else:
            user = self.AllUsers(user_name)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUsers(user.id, addr, port, datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(datetime.now(), addr, port, user.id)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, user_name):

        user = self.session.query(self.AllUsers).filter_by(
            user_name=user_name).first()
        self.session.query(self.ActiveUsers).filter_by(
            user_id=user.id).delete()
        self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.AllUsers.user_name, self.AllUsers.last_login,)
        return query.all()

    def active_users_list(self):
        query = self.session.query(
            self.AllUsers.user_name,
            self.ActiveUsers.addr,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)

        return query.all()

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


# if __name__ == '__main__':
    # test_db = ServerDb()
    #
    # test_db.user_login('client1', '192.168.0.3', 5555)
    # test_db.user_login('client2', '192.168.0.5', 4444)
    #
    # print(test_db.active_users_list())
    #
    # test_db.user_logout('client1')
    # print(test_db.active_users_list())
    # test_db.user_logout('client2')
    # print(test_db.active_users_list())
