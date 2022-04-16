"""
Функции кодирования и отправки, а также приема и декодирования сообщений
"""
import json
from errors import IncorrectDataRecivedError, NonDictInputError
from .variables import MAX_MESSAGE_LEN, ENCODING
import sys
sys.path.append('../')
from log_decorator import log


@log
def send_message(socket, message):
    """
    функция кодирования и отправки сообщения, получает словарь и отправляет
    байты в формате json.
    :param socket:
    :param message: dict
    :return: bytes(in json)
    """
    if not isinstance(message, dict):
        raise NonDictInputError
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    socket.send(encoded_message)


@log
def read_message(socket):
    """
    функция приёма и декодирования сообщения, принимает байты, возвращает
    словарь,
    :param socket:
    :return: dict
    """
    encoded_response = socket.recv(MAX_MESSAGE_LEN)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        else:
            raise IncorrectDataRecivedError
    else:
        raise IncorrectDataRecivedError
