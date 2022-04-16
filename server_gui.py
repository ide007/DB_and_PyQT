import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QDesktopWidget, \
    QLabel, QTableView, QDialog, QLineEdit, QPushButton, QFileDialog, \
    QApplication, QMessageBox

from common.variables import WINDOW_HEIGHT, WINDOW_WIGHT


#  GUI - создание графической таблицы
def gui_create_model(database):
    active_users = database.active_users_list()
    list = QStandardItemModel()
    list.setHorizontalHeaderLabels(
        ['Клиент', 'IP - адрес', 'Порт', 'Время подключения'])
    for row in active_users:
        user, ip, port, time = row
        user = QStandardItem(user)
        user.setEditable(False)
        ip = QStandardItem(ip)
        ip.setEditable(False)
        port = QStandardItem(str(port))
        port.setEditable(False)
        # Уберём миллисекунды из строки времени
        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)
        list.appendRow([user, ip, port, time])
    return list


# GUI - для заполнения таблицы истории сообщений
def create_stat_model(database):
    # Список сообщений из базы для таблицы
    hist_list = database.message_history()

    # Объект модели данных:
    list = QStandardItemModel()
    list.setHorizontalHeaderLabels(
        ['Имя Клиента', 'Последний раз входил', 'Сообщений отправлено',
         'Сообщений получено'])
    for row in hist_list:
        user, last_seen, sent, recvd = row
        user = QStandardItem(user)
        user.setEditable(False)
        last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
        last_seen.setEditable(False)
        sent = QStandardItem(str(sent))
        sent.setEditable(False)
        recvd = QStandardItem(str(recvd))
        recvd.setEditable(False)
        list.appendRow([user, last_seen, sent, recvd])
    return list


# Класс основного окна
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # кнопка выхода
        exitAction = QAction('Выход', self)
        exitAction.setShortcut('Ctrl + Q')
        exitAction.triggered.connect(qApp.quit)

        # Кнопка обновления списока пользователей
        self.refresh_button = QAction('Обновить список', self)

        # Кнопка настроек сервера
        self.config_btn = QAction('Настройки сервера', self)

        # Кнопка вывести историю сообщений
        self.show_history_button = QAction('История клиентов', self)

        # Статусбар
        self.statusBar()

        # Тулбар
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.config_btn)
        self.toolbar.addAction(self.show_history_button)

        # Настройка геометрии окна
        self.setFixedSize(WINDOW_WIGHT, WINDOW_HEIGHT)
        self.screen = QDesktopWidget()
        self.padding_left = int((self.screen.width() - WINDOW_WIGHT)/2)
        self.padding_top = int((self.screen.height() - WINDOW_HEIGHT)/2)
        self.move(self.padding_left, self.padding_top)
        self.setWindowTitle('Мессенджер сервер alfa-version')

        # Надпись о том, что ниже список подключённых клиентов
        self.label = QLabel('Список подключённых клиентов:', self)
        self.label.setFixedSize(240, 15)
        self.label.move(15, 30)

        # Окно со списком подключённых клиентов.
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(20, 50)
        self.active_clients_table.setFixedSize(780, 400)

        # Последним параметром отображаем окно.
        self.show()


# Класс окна с историей пользователей
class HistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна:
        self.setWindowTitle('Статистика пользователей')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # Лист с историей
        self.history_table = QTableView(self)
        self.history_table.move(15, 15)
        self.history_table.setFixedSize(580, 620)

        self.show()


# Класс окна настроек
class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна
        self.setFixedSize(400, 260)
        self.setWindowTitle('Настройки сервера')

        # Надпись о файле базы данных:
        self.db_path_label = QLabel('Путь до файла базы данных: ', self)
        self.db_path_label.move(15, 15)
        self.db_path_label.setFixedSize(250, 20)

        # Строка с путём базы
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(15, 30)
        self.db_path.setReadOnly(True)

        # Кнопка выбора пути.
        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.move(300, 30)

        # Функция обработчик открытия окна выбора папки
        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        # Метка с именем поля файла базы данных
        self.db_file_label = QLabel('Имя файла базы данных: ', self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        # Поле для ввода имени файла
        self.db_file = QLineEdit(self)
        self.db_file.move(200, 70)
        self.db_file.setFixedSize(170, 20)

        # Метка с номером порта
        self.port_label = QLabel('Порт для соединений:  ', self)
        self.port_label.move(10, 120)
        self.port_label.setFixedSize(190, 20)

        # Поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.move(200, 110)
        self.port.setFixedSize(160, 20)

        # Метка с адресом для соединений
        self.ip_label = QLabel('IP для подключения пользователей: ', self)
        self.ip_label.move(15, 155)
        self.ip_label.setFixedSize(190, 15)

        # Метка с напоминанием о пустом поле.
        self.ip_label_note = QLabel('Оставьте поле пустым, чтобы \n'
                                    'принимать соединения с любых '
                                    'адресов.', self)
        self.ip_label_note.move(15, 170)
        self.ip_label_note.setFixedSize(600, 30)

        # Поле для ввода ip
        self.ip = QLineEdit(self)
        self.ip.move(200, 150)
        self.ip.setFixedSize(160, 20)

        # Кнопка сохранения настроек
        self.save_btn = QPushButton(' Сохранить ' , self)
        self.save_btn.move(190 , 220)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    message = QMessageBox
    dial = ConfigWindow()

    app.exec_()
