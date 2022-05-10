"""
Модуль декоратора для логирования @log, фиксирующий обращение
к декорируемой функции. Он сохраняет ее имя и аргументы.
В декораторе @log реализована функция фиксации, из которой была вызвана
декорируемый метод или функция.
"""
import logging
import sys
import inspect

# Инициализация логера.
# Метод определения модуля, источника запуска.
if sys.argv[0].find('client.py') == -1:
    # Если не клиент, то сервер!
    LOGGER = logging.getLogger('server')
else:
    # Раз не сервер, то клиент.
    LOGGER = logging.getLogger('client')


def log(func):
    """Декоратор"""
    def wrap(*args, **kwargs):
        """Обертка"""
        result = func(*args, **kwargs)
        LOGGER.debug(f'Функция-"{func.__name__}" была вызвана из модуля-'
                     f'"{func.__module__}" и инициирован из функцией-'
                     f'"{inspect.stack()[1][3]}", с параметрами "{args}",'
                     f' "{kwargs}".')
        return result   # возврат результата работы декорируемой функции
    return wrap     # результат работы декоратора
