import dis


# Мета класс для проверки объекта сервер
class ServerVerifier(type):
    def __init__(cls, cls_name, bases, cls_dict):
        # Список методов, которые используются в функциях класса:
        methods = []
        # Атрибуты, вызываемые функциями классов
        attrs = []
        for func in cls_dict:
            # Пробуем
            try:
                ret = dis.get_instructions(cls_dict[func])
                # Если не функция, то ловим исключение
            except TypeError:
                pass
            else:
                # Раз функция разбираем код, получая используемые методы и
                # атрибуты.
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        # Если обнаружено использование недопустимого метода connect, бросаем
        # исключение:
        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо в '
                            'серверном классе')
        # Если сокет не инициализировался константами SOCK_STREAM(TCP)
        # AF_INET(IPv4), тоже исключение.
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(cls_name, bases, cls_dict)


# Мета класс для проверки объекта "клиента"
class ClientVerifier(type):

    def __init__(cls, clsname, bases, clsdict):
        # Список методов, которые используются в функциях класса:
        methods = []
        for func in clsdict:
            # Пробуем
            try:
                ret = dis.get_instructions(clsdict[func])
                # Если не функция то ловим исключение
            except TypeError:
                pass
            else:
                # Раз функция разбираем код, получая используемые методы.
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        # Если обнаружено использование недопустимого метода accept, listen,
        # socket бросаем исключение:
        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('В классе обнаружено использование '
                                'запрещённого метода')
        # Вызов read_message или send_message из utils считаем корректным
        # использованием сокетов
        if 'read_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с'
                            ' сокетами.')
        super().__init__(clsname, bases, clsdict)
