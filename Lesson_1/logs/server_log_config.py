import logging
from logging.handlers import TimedRotatingFileHandler
import os


server_logger = logging.getLogger('server')
PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'server.log')
formatter = logging.Formatter(
    '%(asctime)s %(levelname)-8s %(funcName)s %(message)s',
    datefmt='%Y %b %d %H:%M:%S',
)

file_hand = logging.handlers.TimedRotatingFileHandler(
    filename=PATH, when='D', interval=1, encoding='utf-8', delay=True,
    backupCount=31, atTime=None
)

file_hand.setFormatter(formatter)
file_hand.setLevel(logging.DEBUG)

server_logger.addHandler(file_hand)
server_logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    server_logger.addHandler(console)
    server_logger.info('Тестовый запуск логирования')
