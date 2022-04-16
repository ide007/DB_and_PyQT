import dis


# Мета класс для проверки объекта сервер
class ServerVerifier(type):

    def __init__(cls, cls_name, bases, cls_dict):
        # собираем список методов и атрибутов используемых в классе
        methods = []
        attrs = []

        for func in cls_dict:
            try:
                getter = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for i in getter:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)

                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)

        if 'connect' in methods:
            raise TypeError('Использование метода "connect" недопустимо для '
                            'серверного класса.')
        if not ('SOCK_STREAM' in attrs or methods and 'AF_INET' in attrs
                or methods ):
            raise TypeError('Некорректная инициализация серверного сокета.')
        super().__init__(cls_name, bases, cls_dict)


# Мета класс для проверки объекта "клиента"
class ClientVerifier(type):

    def __init__(cls, cls_name, bases, cls_dict):
        # собираем список методов класса
        methods = []

        for func in cls_dict:
            try:
                getter = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for i in getter:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)

        for method in ('accept', 'listen', 'socket'):
            if method in methods:
                raise TypeError('В классе обнаружено использование '
                                'запрещенного метода.')

        # if 'send_message' in methods or 'read_message' in methods:
        #     pass
        # else:
        #     raise TypeError('Отсутствуют вызовы функций, работающих с '
        #                     'сокетами')

        super().__init__(cls_name, bases, cls_dict)
