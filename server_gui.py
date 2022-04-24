import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, \
    QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog, QMessageBox, QDesktopWidget
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
import os


# GUI - Создание таблицы QModel, для отображения в окне программы.
from common.variables import WINDOW_WIGHT, WINDOW_HEIGHT


def gui_create_model(database):
    list_users = database.active_users_list()
    list = QStandardItemModel()
    list.setHorizontalHeaderLabels(['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
    for row in list_users:
        user, ip, port, time = row
        user = QStandardItem(user)
        user.setEditable(False)
        ip = QStandardItem(ip)
        ip.setEditable(False)
        port = QStandardItem(str(port))
        port.setEditable(False)
        # Уберём милисекунды из строки времени, т.к. такая точность не требуется.
        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)
        list.appendRow([user, ip, port, time])
    return list


# GUI - Функция реализующая заполнение таблицы историей сообщений.
def create_stat_model(database):
    # Список записей из базы
    hist_list = database.message_history()

    # Объект модели данных:
    list = QStandardItemModel()
    list.setHorizontalHeaderLabels(
        ['Имя Клиента', 'Последний раз входил', 'Сообщений отправлено', 'Сообщений получено'])
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
        # Кнопка выхода
        exitAction = QAction('Выход', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(qApp.quit)

        # Кнопка обновить список клиентов
        self.refresh_button = QAction('Обновить список', self)

        # Кнопка настроек сервера
        self.config_btn = QAction('Настройки сервера' , self)

        # Кнопка вывести историю сообщений
        self.show_history_button = QAction('История клиентов', self)

        # Статусбар
        self.statusBar()

        # Тулбар
        self.toolbar = self.addToolBar('MainBar')
        self.toolbar.addAction(exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_btn)

        # Настройки геометрии основного окна
        # Поскольку работать с динамическими размерами мы не умеем, и мало времени на изучение, размер окна фиксирован.
        self.setFixedSize(WINDOW_WIGHT, WINDOW_HEIGHT)
        self.screen = QDesktopWidget()
        self.padding_left = int((self.screen.width() - WINDOW_WIGHT) / 2)
        self.padding_top = int((self.screen.height() - WINDOW_HEIGHT) / 2)
        self.move(self.padding_left, self.padding_top)
        self.setWindowTitle('Messaging Server alpha release')

        # Надпись о том, что ниже список подключённых клиентов
        self.label = QLabel('Список подключённых клиентов:', self)
        self.label.setFixedSize(240, 15)
        self.label.move(15, 30)

        # Окно со списком подключённых клиентов.
        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(20, 50)
        self.active_clients_table.setFixedSize(int(WINDOW_WIGHT * 0.8),
                                               int(WINDOW_HEIGHT * 0.75))

        # Последним параметром отображаем окно.
        self.show()


# Класс окна с историей пользователей
class HistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна:
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(600, 650)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Кнапка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 600)
        self.close_button.clicked.connect(self.close)

        # Лист с собственно историей
        self.history_table = QTableView(self)
        self.history_table.move(15, 15)
        self.history_table.setFixedSize(570, 570)

        self.show()


# Класс окна настроек
class ConfigWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Настройки окна
        self.setFixedSize(500, 320)
        self.setWindowTitle('Настройки сервера')

        # Надпись о файле базы данных:
        self.db_path_label = QLabel('Путь до файла базы данных: ', self)
        self.db_path_label.move(20, 5)
        self.db_path_label.setFixedSize(250, 30)

        # Строка с путём базы
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(320, 30)
        self.db_path.move(20, 35)
        self.db_path.setReadOnly(True)

        # Кнопка выбора пути.
        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.move(350, 32)

        # Функция обработчик открытия окна выбора папки
        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.clear()
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        # Метка с именем поля файла базы данных
        self.db_file_label = QLabel('Имя файла базы данных: ', self)
        self.db_file_label.move(20, 75)
        self.db_file_label.setFixedSize(200, 25)

        # Поле для ввода имени файла
        self.db_file = QLineEdit(self)
        self.db_file.move(300, 75)
        self.db_file.setFixedSize(170 , 25)

        # Метка с номером порта
        self.port_label = QLabel('Номер порта для соединений:', self)
        self.port_label.move(20, 107)
        self.port_label.setFixedSize(200, 25)

        # Поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.move(300, 110)
        self.port.setFixedSize(120, 25)

        # Метка с адресом для соединений
        self.ip_label = QLabel('С какого IP принимаем соединения:', self)
        self.ip_label.move(20, 145)
        self.ip_label.setFixedSize(300, 25)

        # Метка с напоминанием о пустом поле.
        self.ip_label_note = QLabel(' оставьте это поле пустым, чтобы\n принимать соединения с любых адресов.', self)
        self.ip_label_note.move(20, 165)
        self.ip_label_note.setFixedSize(600, 50)

        # Поле для ввода ip
        self.ip = QLineEdit(self)
        self.ip.move(300, 145)
        self.ip.setFixedSize(170, 25)

        # Кнопка сохранения настроек
        self.save_btn = QPushButton('Сохранить' , self)
        self.save_btn.move(120 , 250)

        # Кнапка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(275, 250)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    message = QMessageBox
    # dial = ConfigWindow()
    dial = HistoryWindow()
    # dial = MainWindow()
    app.exec_()
