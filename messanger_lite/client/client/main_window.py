"""Модуль основного пользовательского окна."""
import logging

from base64 import b64encode, b64decode
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, Qt
from json import JSONDecodeError
from messanger_lite.client.client.main_window_conv import Ui_MainClientWindow
from messanger_lite.client.client.add_contact import AddContactDialog
from messanger_lite.client.client.del_contact import DelContactDialog
from messanger_lite.client.common.errors import ServerError
from messanger_lite.client.common.variables import ENCODING, MESSAGE_TEXT, SENDER

logger = logging.getLogger('client')


class ClientMainWindow(QMainWindow):
    """
    Класс - основное окно пользователя.
    Содержит всю основную логику работы клиентского модуля.
    """

    def __init__(self, database, transport, keys):
        super().__init__()
        # основные переменные
        self.database = database
        self.transport = transport

        # объект - дешифровщик соединения с ключом
        self.decrypter = PKCS1_OAEP.new(keys)

        # Загружаем конфигурацию окна из файла main_window_conv.py
        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        # Кнопка "Выход"
        self.ui.menu_exit.triggered.connect(qApp.exit)

        # Кнопка отправить сообщение
        self.ui.btn_send.clicked.connect(self.send_message)

        # "добавить контакт"
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        # Удалить контакт
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        # Дополнительные требующиеся атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        # Двойной клик по листу контактов отправляется в обработчик
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def set_disabled_input(self):
        """Метод для деактивации поля ввода."""
        # Надпись  - получатель.
        self.ui.label_new_message.setText('Для выбора получателя дважды '
                                          'кликните на нем в окне контактов.')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        # Поле ввода и кнопка отправки неактивны до выбора получателя.
        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

    def history_list_update(self):
        """Метод для заполнения историей переписки с выбранным собеседником."""
        # Получаем историю сортированную по дате
        list = sorted(self.database.get_history(self.current_chat),
                      key=lambda item: item[3])
        # Если модель не создана, создадим.
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        # Очистим от старых записей
        self.history_model.clear()
        # Берём не более 15 последних записей.
        length = len(list)
        start_index = 0
        if length > 15:
            start_index = length - 15
        # Заполнение модели записями, так-же стоит разделить входящие и
        # исходящие выравниванием и разным фоном. Записи в обратном порядке,
        # поэтому выбираем их с конца и не более 15
        for i in range(start_index, length):
            item = list[i]
            if item[1] == 'in':
                mess = QStandardItem(f'Входящее от '
                                     f'{item[3].replace(microsecond=0)}:\n'
                                     f' {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Исходящее от '
                                     f'{item[3].replace(microsecond=0)}:\n'
                                     f' {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    def select_active_user(self):
        """Метод обработчик двойного клика по контакту"""
        # Выбранный пользователем (даблклик) находится в выделенном элементе в
        # QListView
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        # вызываем основную функцию
        self.set_active_user()

    def set_active_user(self):
        """Метод обработчик события двойного клика по списку контактов."""
        # Запрашиваем публичный ключ пользователя и создаём объект шифрования
        try:
            self.current_chat_key = self.transport.key_request(
                self.current_chat)
            logger.debug(f'Загружен открытый ключ для {self.current_chat}')
            if self.current_chat_key:
                self.encryptor = PKCS1_OAEP.new(RSA.import_key(
                    self.current_chat_key))
        except (OSError, JSONDecodeError):
            self.current_chat_key = None
            self.encryptor = None
            logger.debug(f'Не удалось получить ключ для {self.current_chat}')

        # При отсутствии ключа шифрования вызываем ошибку, и сообщаем о
        # невозможности начать чат с выбранным пользователем
        if not self.current_chat_key:
            self.messages.warning(self, 'Ошибка', 'Для выбранного контакта'
                                                  'нет ключа шифрования.')
            return

        # Ставим надпись и активируем кнопки
        self.ui.label_new_message.setText(f'Введите сообщение для'
                                          f' {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)

        # Заполняем окно историю сообщений по требуемому пользователю.
        self.history_list_update()

    def clients_list_update(self):
        """Метод для обновления списка контактов."""
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def add_contact_window(self):
        """Метод для добавления контактов - открываем диалоговое окно."""
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(
            lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    def add_contact_action(self, item):
        """Метод для обработки нажатия кнопки 'Добавить'."""
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        """
        Метод добавляющий контакт в базу данных на сервере и клиенте.
        После записи в БД обновляем и содержимое окна.
        """
        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с'
                                                       ' сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            logger.info(f'Успешно добавлен контакт {new_contact}')
            self.messages.information(self, 'Успех', 'Контакт добавлен.')

    def delete_contact_window(self):
        """Метод для удаления контакта - открываем диалоговое окно."""
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(
            lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        """
        Метод удаляющий контакт из базы данных на сервере и клиенте.
        После обновления БД обновляем и содержимое окна.
        """
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с'
                                                       ' сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.del_contact(selected)
            self.clients_list_update()
            logger.info(f'Успешно удалён контакт {selected}')
            self.messages.information(self, 'Успех', 'Контакт успешно удалён.')
            item.close()
            # Если удалён активный пользователь, то деактивируем поля ввода.
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    def send_message(self):
        """
        Функция для отправки сообщения выбранному пользователю.
        Проводим шифрование сообщения с последующей отправкой.
        """
        # Текст в поле, проверяем что поле не пустое затем забирается сообщение
        # и поле очищается
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return

        # Шифруем сообщение ключом получателя и упаковываем в base64.
        message_text_encrypted = self.encryptor.encrypt(
            message_text.encode(ENCODING))
        message_text_encrypted_base64 = b64encode(message_text_encrypted)

        try:
            self.transport.send_message(
                self.current_chat,
                message_text_encrypted_base64.decode('ascii'))
            pass
        except ServerError as err:
            self.messages.critical(self, 'Ошибка', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с'
                                                       ' сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с'
                                                   ' сервером!')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            logger.debug(f'Отправлено сообщение для {self.current_chat}:'
                         f' {message_text}')
            self.history_list_update()

    # Слот приёма нового сообщений
    @pyqtSlot(dict)
    def message(self, message):
        """
        Слот обработчик входящих сообщений, выполняет дешифровку
        сообщений и их сохранение в истории сообщений.
        Запрашивает пользователя если пришло сообщение не от текущего
        собеседника. При необходимости меняет собеседника.
        """
        # Получаем строку в байтовом виде
        encrypted_message = b64decode(message[MESSAGE_TEXT])

        # Декодируем строку, при ошибке выдаём сообщение и завершаем функцию
        try:
            decrypted_message = self.decrypter.decrypt(encrypted_message)
        except (ValueError, TypeError):
            self.messages.warning(self, 'Ошибка',
                                  'Не удалось декодировать сообщение.')
            return
        # В случаи успешного декодирования сохраняем его в базу и обновляем
        # историю сообщений или открываем новый чат.
        self.database.save_message(self.current_chat, 'in',
                                   decrypted_message.decode(ENCODING))
        sender = message[SENDER]
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # Проверим есть ли такой пользователь у нас в контактах:
            if self.database.check_contact(sender):
                # Если пользователь есть, следом спрашиваем 'открыть с ним чат'
                # и открываем при желании
                if self.messages.question(
                    self, 'Новое сообщение',
                    f'Получено новое сообщение от {sender}, открыть чат с'
                    f' ним?', QMessageBox.Yes,
                        QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print('NO')
                # Раз нет, спрашиваем хотим ли добавить юзера в контакты.
                if self.messages.question(
                    self, 'Новое сообщение',
                    f'Получено новое сообщение от {sender}.\n Данного '
                    f'пользователя нет в вашем контакт-листе.\n Добавить в'
                    f' контакты и открыть чат с ним?',
                        QMessageBox.Yes,
                        QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    # Нужно заново сохранить сообщение, иначе оно будет
                    # потеряно, т.к. на момент предыдущего вызова контакта не
                    # было.
                    self.database.save_message(
                        self.current_chat, 'in',
                        decrypted_message.decode(ENCODING))
                    self.set_active_user()

    # Слот потери соединения. Выдаёт сообщение об ошибке и завершает работу
    # приложения
    @pyqtSlot()
    def connection_lost(self):
        """
        Слот обработчик потери соединения с сервером.
        Выдаёт окно предупреждение и завершает работу приложения.
        """
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с'
                                                       ' сервером. ')
        self.close()

    @pyqtSlot()
    def sig_205(self):
        """Слот выполняющий обновление баз данных по команде сервера."""
        if self.current_chat and not self.database.check_user(
                self.current_chat):
            self.messages.warning(
                self,
                'Сочувствую',
                'К сожалению собеседник был удалён с сервера.')
            self.set_disabled_input()
            self.current_chat = None
        self.clients_list_update()

    def make_connection(self, trans_obj):
        """Метод обеспечивающий соединение сигналов и слотов."""
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)
        trans_obj.message_205.connect(self.sig_205)