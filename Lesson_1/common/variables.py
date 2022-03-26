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
