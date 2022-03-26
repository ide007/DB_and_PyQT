"""
Продолжая задачу логирования, реализовать декоратор @log, фиксирующий обращение
к декорируемой функции. Он сохраняет ее имя и аргументы.
В декораторе @log реализовать фиксацию функции, из которой была вызвана
декорированная. Если имеется такой код:
@log
def func_z():
 pass

def main():
 func_z()
...в логе должна быть отражена информация:
"<дата-время> Функция func_z() вызвана из функции main"
"""
import logging
import sys
import inspect

if sys.argv[0].find('client.py') == -1:
    LOGGER = logging.getLogger('server')
else:
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
        return result   # возврат результата работы декарируемой функции
    return wrap     # результат работы декотарора
