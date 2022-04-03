from dis import get_instructions


class ClientVerifier(type):

    def __init__(self, cls_name, bases, cls_dict):
        # собираем список методов класса
        methods = []

        for func in cls_dict:
            try:
                getter = get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for i in getter:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)

        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('В классе обнаруженно использование '
                                'запрещенного метода.')

        if 'send_message' in methods or 'read_message' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами')

        super().__init__(cls_name, bases, cls_dict)


class ServerVerifier(type):

    def __init__(self, cls_name, bases, cls_dict):
        # собираем список методов и атрибутов
        methods = []
        attrs = []

        for func in cls_dict:
            try:
                getter = get_instructions(cls_dict[func])
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
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация серверного сокета.')
        super().__init__(cls_name, bases, cls_dict)
