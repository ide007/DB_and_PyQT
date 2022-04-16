import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import ACTION, ACCOUNT_NAME, ERROR, PRESENCE, RESPONSE,\
    TIME, USER
from client import create_presence, server_answer


class TestClass(unittest.TestCase):
    """ Класс с тестами """

    def test_def_presence(self):
        """Тест коректности запроса"""
        test = create_presence()
        test[TIME] = 1
        self.assertEqual(test, {
            ACTION: PRESENCE, TIME: 1, USER: {ACCOUNT_NAME: 'Guest'}
        })

    def test_200_server_answer(self):
        """Тест корректности разбора ответа 200"""
        self.assertEqual(server_answer({RESPONSE: 200}), '200: OK')

    def test_400_server_answer(self):
        """Тест корректности разбора ответа 400"""
        self.assertEqual(server_answer({
            RESPONSE: 400, ERROR: 'Bad Request'
        }), '400: Bad Request')

    def test_wrong_account_name(self):
        """Тест коректности запроса"""
        test = create_presence(account_name='wrong name')
        test[TIME] = 1
        self.assertRaises(ValueError, server_answer, {
            USER: {ACCOUNT_NAME: 'wrong name'}
        })

    def test_no_response(self):
        """Тест выброса исключения (без поля 'RESPONSE')"""
        self.assertRaises(ValueError, server_answer, {ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
