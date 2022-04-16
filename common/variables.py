""" Константы для проекта """

# порт по умолчанию
DEFAULT_PORT = 7777

# IP-адрес по умолчанию
DEFAULT_IP_ADDRESS = '127.0.0.1'

# Максимальная длина очереди на подключение
MAX_CONNECTIONS = 5

# Максимальная длина сообщения в байтах
MAX_MESSAGE_LEN = 1024

# Применяемая кодировка
ENCODING = 'utf-8'

# БД для хранения данных сервера
SERVER_DATABASE = 'sqlite:///server_base.db3'

# База данных для хранения данных сервера:
SERVER_CONFIG = 'server.ini'

# Протокол JIM, основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'

# Протокол JIM, прочие ключи
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'message_text'
EXIT = 'exit'
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'

# настройки окна
WINDOW_WIGHT = 1024
WINDOW_HEIGHT = 768

# Словари ответов:
# 200
RESPONSE_200 = {RESPONSE: 200}

# 202
RESPONSE_202 = {RESPONSE: 202, LIST_INFO: None}

# 400
RESPONSE_400 = {RESPONSE: 400, ERROR: None}
