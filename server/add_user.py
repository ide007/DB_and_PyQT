"""Модуль регистрации пользователей на сервере."""
import binascii
import hashlib

from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, \
    QMessageBox
from PyQt5.QtCore import Qt


class RegisterUser(QDialog):
    """Класс - регистрации пользователей на сервере. Вывод диалогового окна."""

    def __init__(self, database, server):
        super().__init__()

        self.database = database
        self.server = server

        self.setWindowTitle('Регистрация')
        self.setFixedSize(200, 200)
        self.Modal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.label_username = QLabel('Введите имя пользователя:', self)
        self.label_username.move(10, 10)
        self.setFixedSize(155, 15)

        self.client_name = QLineEdit(self)
        self.client_name.move(10, 30)
        self.client_name.setFixedSize(155, 20)

        self.label_password = QLineEdit('Введите пароль: ')
        self.label_password.move(10, 55)
        self.label_password.setFixedSize(150, 15)

        self.client_pass = QLineEdit(self)
        self.client_pass.move(10, 75)
        self.client_pass.setEchoMode(QLineEdit.Password)

        self.btn_ok = QPushButton('Сохранить', self)
        self.btn_ok.move(10, 150)
        self.btn_ok.clicked.connect(self.save_data)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(90, 150)
        self.btn_cancel.clicked.connect(self.close)

        self.messages = QMessageBox()

        self.show()

    def save_data(self):
        """
        Метод проверки правильности ввода и сохранения в базу нового
        пользователя.
        """
        if not self.client_name.text():
            self.messages.critical(
                self, 'Ошибка', 'Не указано имя пользователя.')
            return
        elif self.client_passwd.text() != self.client_conf.text():
            self.messages.critical(
                self, 'Ошибка', 'Введённые пароли не совпадают.')
            return
        elif self.database.check_user(self.client_name.text()):
            self.messages.critical(
                self, 'Ошибка', 'Пользователь уже существует.')
            return
        else:
            # Генерируем хэш пароля, в качестве соли будем использовать логин в
            # нижнем регистре.
            passwd_bytes = self.client_passwd.text().encode('utf-8')
            salt = self.client_name.text().lower().encode('utf-8')
            passwd_hash = hashlib.pbkdf2_hmac(
                'sha512', passwd_bytes, salt, 10000)
            self.database.add_user(
                self.client_name.text(),
                binascii.hexlify(passwd_hash))
            self.messages.information(
                self, 'Успех', 'Пользователь успешно зарегистрирован.')
            # Рассылаем клиентам сообщение о необходимости обновить справочники
            self.server.service_update_lists()
            self.close()
