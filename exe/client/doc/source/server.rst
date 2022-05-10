.. image:: /_static/image.png

Документация серверного модуля
=================================================

Серверный модуль мессенджера.
Хранит публичные ключи клиентов, историю пользователей.
Обрабатывает словари - сообщения.

Модуль поддерживает аргументы командной строки:

1. -p - Порт на котором принимаются соединения
2. -a - Адрес с которого принимаются соединения.
3. --no_gui Запуск только основных функций, без графической оболочки.

* В данном режиме поддерживается только 1 команда: exit - завершение работы.

Примеры использования:

``python server.py -p 8080``

*Запуск сервера на порту 8080*

``python server.py -a localhost``

*Запуск сервера принимающего только соединения с localhost*

``python server.py --no-gui``

*Запуск без графической оболочки*

server.py
~~~~~~~~~

Запускаемый модуль,содержит парсер аргументов командной строки и функционал инициализации приложения.

server. **arg_parser** ()
    Парсер аргументов командной строки, возвращает кортеж из 4 элементов:

    * адрес с которого принимать соединения
    * порт
    * флаг запуска GUI

server. **config_load** ()
    Функция загрузки параметров конфигурации из ini файла.
    В случае отсутствия файла задаются параметры по умолчанию.

core.py
~~~~~~~~~~~

.. automodule:: server.core
    :members:

database.py
~~~~~~~~~~~

.. automodule:: server.database
    :members:

main_window.py
~~~~~~~~~~~~~~

.. autoclass:: server.main_window.MainWindow
    :members:

add_user.py
~~~~~~~~~~~

.. autoclass:: server.add_user.RegisterUser
    :members:

remove_user.py
~~~~~~~~~~~~~~

.. autoclass:: server.remove_user.DelUserDialog
    :members:

config_window.py
~~~~~~~~~~~~~~~~

.. autoclass:: server.config_window.ConfigWindow
    :members:

stat_window.py
~~~~~~~~~~~~~~~~

.. autoclass:: server.stat_window.StatWindow
    :members: