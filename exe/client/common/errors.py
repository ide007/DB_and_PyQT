"""Модуль исключений."""


class ServerError(Exception):
    """Класс - исключение, для обработки ошибок сервера.
    Требует строку с описанием ошибки."""

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


# Ошибка - отсутствует обязательное поле в принятом словаре.
class ReqFieldMissingError(Exception):
    """Класс - исключение, для обработки ошибок отсутствия обязательных полей в
     сообщениях.
    """

    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В принятом словаре отсутствует обязательное ' \
               f'поле {self.missing_field}.'
