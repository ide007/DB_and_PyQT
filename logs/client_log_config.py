import logging
import os
import sys


# создаём регистр
client_logger = logging.getLogger('client')

# Подготовка имени файла для логирования
path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'client.log')

# создаём формировщик логов (formatter)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(funcName)s '
                              '%(message)s',datefmt='%Y %b %d %H:%M:%S',)
file_hand = logging.FileHandler(path, encoding='utf-8')
file_hand.setLevel(logging.DEBUG)

# настраиваем регистратор
file_hand.setFormatter(formatter)
client_logger.addHandler(file_hand)
client_logger.setLevel(10)

if __name__ == '__main__':
    # проверка работоспособности
    stream_hand = logging.StreamHandler(sys.stdout)
    stream_hand.setFormatter(formatter)
    client_logger.addHandler(stream_hand)
    client_logger.info('Тестовое сообщение')
