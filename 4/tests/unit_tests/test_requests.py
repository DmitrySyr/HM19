import functools
import unittest

from server.api import InterestsRequest, ScoreRequest, MethodRequest, ADMIN_LOGIN


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


class TestInterestsRequest(unittest.TestCase):

    @cases([
        {'client_ids': [1, 2, 3]},
    {'client_ids': [1, 2], 'date': '12.12.2012'}
    ])
    def test_good_values(self, value):
        h = InterestsRequest(value)
        self.assertTrue(h.is_valid)

    @cases([
        {'client_ids': [], 'date': '12.12.2012'},
    {'client_ids': [1, 2], 'date': '39.12.2012'},
    {'client_ids': [1, 2], 'date': 'wrong'},
    {'date': '12.12.2012'},
    {'client_ids': [1, 2.6]},
    {'client_ids': [1, 2, 'f']},
    ])
    def test_raises_if_bad_values(self, value):
        h = InterestsRequest(value)
        self.assertFalse(h.is_valid, value)


class TestScoreRequest(unittest.TestCase):

    @cases([
        {'first_name': 'first_name', 'last_name': 'last_name'},
    {'email': 'bk.bk@bk.ru', 'phone': '71236549871'},
    {'email': 'bk.bk@bk.ru', 'phone': 79517531268},
    {'birthday': '12.12.1975', 'gender': 0},
    {'birthday': '12.12.1975', 'gender': 1},
    {'birthday': '12.12.1975', 'gender': 2},
    ])
    def test_good_values(self, value):
        h = ScoreRequest(value)
        self.assertTrue(h.is_valid)

    @cases([
        {'first_name': '', 'last_name': 'last_name'},
    {'email': 'bk.bk@bk.ru', 'phone': '7123649871'},
    {'email': 'bk.bk@bk.ru', 'phone': 789517531268},
    {'birthday': '12.12.1975'},
    {'birthday': '12.12.1975', 'gender': ''},
    {'birthday': '12.12.1975', 'gender': 4},
    ])
    def test_raises_bad_values(self, value):
        h = ScoreRequest(value)
        self.assertFalse(h.is_valid)


class TestMethodRequest(unittest.TestCase):

    @cases([
        {'account': 'first_name', 'login': 'last_name', 'token': 'bk.bk@bk.ru', 
     'arguments': {}, 'method': 'bk.bk@bk.ru'},
    {'login': 'last_name', 'token': 'bk.bk@bk.ru', 'arguments': {},
     'method': 'bk.bk@bk.ru'},
    {'account': 'first_name', 'login': 'last_name', 'token': 'bk.bk@bk.ru', 
     'arguments': {'a': 3}, 'method': ''},   
    {'account': '', 'login': '', 'token': '', 'arguments': {}, 'method': ''},     
    ])
    def test_good_values(self, value):
        h = MethodRequest(value)
        self.assertTrue(h.is_valid, value)   
        self.assertFalse(h.is_admin, value)

    @cases([
        {'login': ADMIN_LOGIN, 'token': 'dsfgsg67567', 'arguments': {'a': 3},
     'method': 'book'},    
    {'account': 'first_name', 'login': ADMIN_LOGIN,'token': 'bk.bk@bk.ru', 
     'arguments': {}, 'method': ''},   
    {'account': '', 'login': ADMIN_LOGIN, 'token': '', 'arguments': {},
     'method': ''},     
    ])
    def test_good_values_admin(self, value):
        h = MethodRequest(value)
        self.assertTrue(h.is_valid, value) 
        self.assertTrue(h.is_admin, value)  

    @cases([
        {'account': 'first_name', 'login': 'last_name',
     'token': 'bk.bk@bk.ru', 'arguments': '', 'method': 'bk.bk@bk.ru'},
    {'token': 'bk.bk@bk.ru', 'arguments': {}, 'method': 'bk.bk@bk.ru'},
    {'account': 'first_name', 'login': 2, 'token': 'bk.bk@bk.ru', 'arguments': {'a': 3},
     'method': ''},   
    {'account': '', '': '', 'token': '', 'arguments': '', 'method': ''},     
    ])
    def test_raises_bad_values(self, value):
        h = MethodRequest(value)
        self.assertFalse(h.is_valid, value)
        self.assertFalse(h.is_admin, value)


if __name__ == "__main__":
    unittest.main()