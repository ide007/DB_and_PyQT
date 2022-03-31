import sys
import os
import unittest
import json
sys.path.append(os.path.join(os.getcwd(), '..'))
from common.utils import send_message, read_message
from common.variables import ACCOUNT_NAME, ACTION, ENCODING, ERROR, \
    MAX_MESSAGE_LEN, PRESENCE, RESPONSE, TIME, USER


class TestSocket:
    """
     Класс с тестами для отправки и полцчения сообщений, при инициализации
     объекта класса требуется словарь с тестовыми данными.
     """
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.received_message = None

    def send(self, message):
        """ Загружает тестовые данные в тестовый сокет """
        json_test_message = json.dumps(self.test_dict)
        self.encoded_message = json_test_message.encode(ENCODING)
        self.received_message = message

    def recv(self, max_len):
        """ Получаем данные из сокета """
        received_message = json.dumps(self.test_dict)
        return received_message.encode(ENCODING)


class TestUtils(unittest.TestCase):
    test_dict = {
        ACTION: PRESENCE,
        TIME: 1.5,
        USER: {ACCOUNT_NAME: 'Test User'}
    }
    test_receive_ok = {RESPONSE: 200}
    test_receive_error = {RESPONSE: 400, ERROR: 'Bad Request'}

    def setUp(self):
        self.test_socket = TestSocket(self.test_dict)
        self.send_test_message = send_message(self.test_socket, self.test_dict)

    def test_send_correct_message(self):
        self.assertEqual(self.test_socket.encoded_message,
                         self.test_socket.received_message)

    def test_send_wrong_dict(self):
        self.assertRaises(TypeError, self.send_test_message, self.test_socket,
                          ['Incorrect dictionary'])

    def test_receive_correct(self):
        test_socket = TestSocket(self.test_receive_ok)
        self.assertEqual(read_message(test_socket),
                         self.test_receive_ok)

    def test_read_response_400(self):
        test_socket = TestSocket(self.test_receive_error)
        self.assertEqual(read_message(test_socket),
                         self.test_receive_error)


if __name__ == '__main__':
    unittest.main()
