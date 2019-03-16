import hashlib
import datetime
import functools
import unittest
import random
import json

from api import (method_handler, ADMIN_LOGIN, SALT, OK, ADMIN_SALT)


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


def set_valid_auth(request):
    if request.get("login") == ADMIN_LOGIN:
        string_to_encode = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
        request["token"] = hashlib.sha512(string_to_encode.encode()).hexdigest()
    else:
        msg = request.get("account", "") + request.get("login", "") + SALT
        request["token"] = hashlib.sha512(msg.encode()).hexdigest()
        
interests = ("cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus")

        
class MockStore(object):
        def __init__(self):
            self.storage = {}
            
            for i in [0, 1, 2, 3]:
                self.storage[f'i:{i}'] = json.dumps(random.sample(interests, 2))

        def set(self, key, value, expired=None):
            self.storage[key] = value

        def get(self, key):
            return self.storage.get(key, None)

        def cache_set(self, key, value, expired=None):
            self.storage[key] = value

        def cache_get(self, key):
            return self.storage.get(key, None)
        
        
class TestEvaluateRequests(unittest.TestCase):
    
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.settings = {}
        self.store = MockStore()    
    
    def get_response(self, request):
        return method_handler({"body": request, "headers": self.headers},
                                  self.context, self.store)    
        
    @cases([
    {'account': 'fun', 'login': 'login',
    'token': '', 'arguments': {'client_ids': [1, 2], 'date': '12.12.2012'},
    'method': 'clients_interests'},  
    ])
    def test_interests_request_good(self, value):
        set_valid_auth(value)
        res, code = self.get_response(value)        
        self.assertTrue(code == OK)
        self.assertTrue(len(res) == len(value['arguments']['client_ids']))
        self.assertTrue(self.context['nclients'] == len(res))
        self.assertCountEqual(
            [i for k in res.values() for i in k if i not in interests], [])
        
    @cases([
    {'account': 'fun', 'login': 'login',
    'token': '', 'arguments': {'first_name': 'first_name', 'last_name': 'last_name'},
    'method': 'online_score'},  
    ])    
    def test_score_request_good(self, value):
        set_valid_auth(value)
        res, code = self.get_response(value)
        self.assertTrue(res == {'score': 0.5})
        self.assertTrue(code == OK)        
    
    @cases([
    {'account': 'fun', 'login': ADMIN_LOGIN,
    'token': '', 'arguments': {'first_name': 'first_name', 'last_name': 'last_name'},
    'method': 'online_score'}  
    ])    
    def test_score_request_good_admin(self, value):
        set_valid_auth(value)
        res, code = self.get_response(value)  
        self.assertTrue(res == {'score': 42})
        self.assertTrue(code == OK)
        
        
if __name__ == "__main__":
    unittest.main()