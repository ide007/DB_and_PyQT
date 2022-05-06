from server import check_and_create_answer_to_client
from common.variables import ACTION, ACCOUNT_NAME, ERROR, PRESENCE, RESPONSE,\
    TIME, USER
import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))


class TestServer(unittest.TestCase):
    """ Класс с тестами """
    correct_dict = {RESPONSE: 200}
    error_dict = {RESPONSE: 400, ERROR: 'Bad Request'}

    def test_ok_check(self):
        self.assertEqual(check_and_create_answer_to_client({
            ACTION: PRESENCE, TIME: 1, USER: {
                ACCOUNT_NAME: 'Guest'
            }
        }), self.correct_dict)

    def test_no_action(self):
        self.assertEqual(check_and_create_answer_to_client({
            TIME: 1, USER: {ACCOUNT_NAME: 'Guest'}
        }), self.error_dict)

    def test_wrong_action(self):
        self.assertEqual(check_and_create_answer_to_client({
            ACTION: 'Test wrong action', TIME: 1, USER: {ACCOUNT_NAME: 'Guest', }
        }), self.error_dict)

    def test_no_time_in_response(self):
        self.assertEqual(check_and_create_answer_to_client({
            ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}
        }), self.error_dict)

    def test_no_user(self):
        self.assertEqual(check_and_create_answer_to_client({
            ACTION: PRESENCE, TIME: 1
        }), self.error_dict)

    def test_wrong_account_name(self):
        self.assertEqual(check_and_create_answer_to_client({
            ACTION: PRESENCE, TIME: 1, USER: {ACCOUNT_NAME: 'Wrong name'}
        }), self.error_dict)


if __name__ == '__main__':
    unittest.main()
