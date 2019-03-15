import unittest
import functools

from unittest.mock import patch
from datetime import datetime

from store import Store


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            print(*args)
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


class TestStore(unittest.TestCase):
    
    @patch('redis.Redis', autospec=True)
    @cases([
            ('value', 1), 
            ('score', 15), 
            ('interests', "['swimming, 'jogging']"),
            ('empty_expire', 90),
            ])
    def test_store_methods_set_get(self, _, key, value):
        store = Store()
        store.store.append.return_value = None
        store.store.get.return_value = value
        store.set(key, value)
        store.store.append.assert_called_with(key, value) 
        self.assertEqual(value, store.get(key), (key, value))  
        store.store.get.assert_called_with(key)
        
        
    @patch('redis.Redis', autospec=True)
    @cases([
            ('value', 1, 120), 
            ('score', 15, 60), 
            ('interests', "['swimming, 'jogging']", 90),
            ('empty_expire', 90, 5),
            ])
    def test_store_methods_set_get_with_expir(self, _, key, value, expir):
        store = Store()
        store.store.append.return_value = None
        store.store.get.return_value = value
        store.set(key, value, expir)
        store.store.append.assert_called_with(key, value) 
        store.store.expireat.assert_called_with(key, 
                                                int(datetime.now().timestamp()) + expir) 
        self.assertEqual(value, store.get(key), (key, value))  
        store.store.get.assert_called_with(key)  
        
    @patch('redis.Redis', autospec=True)
    @cases([
            ('value', 1, 120), 
            ('score', 15, 60), 
            ('interests', "['swimming, 'jogging']", 90),
            ('empty_expire', 90, 5),
            ])
    def test_store_methods_cache_set_cache_get_with_expir(self, _, key, value, expir):
        store = Store()
        store.store.append.return_value = None
        store.store.get.return_value = value
        store.cache_set(key, value, expir)
        store.store.append.assert_called_with(key, value) 
        store.store.expireat.assert_called_with(key, 
                                                int(datetime.now().timestamp()) + expir) 
        self.assertEqual(value, store.cache_get(key), (key, value))  
        store.store.get.assert_called_with(key)  
    
        
    @patch('redis.Redis', autospec=True)
    @cases([
            ('value', 1, 1), 
            ('score', 15, 1), 
            ('interests', "['swimming, 'jogging']", 1),
            ('empty_expire', 90, 1),
            ])
    def test_store_methods_set_get_with_expired_expir(self, _, key, value, expir):
        store = Store()
        store.store.append.return_value = None
        store.store.get.return_value = None
        store.set(key, value, expir)
        store.store.append.assert_called_with(key, value) 
        store.store.expireat.assert_called_with(key, 
                                                int(datetime.now().timestamp()) + expir) 
        self.assertEqual(None, store.get(key), (key, value))  
        store.store.get.assert_called_with(key)   
        
    
    @patch('redis.Redis', autospec=True)
    @cases([
            ('value', 1, 1), 
            ('score', 15, 1), 
            ('interests', "['swimming, 'jogging']", 1),
            ('empty_expire', 90, 1),
            ])
    def test_store_methods_set_get_with_repetitions(self, _, key, value, expir):
        side_effect = [Exception() for i in range(5)]
        side_effect.append(value)
        store = Store()
        store.store.append.return_value = None
        store.store.get.side_effect = side_effect
        store.set(key, value, expir)
        store.store.append.assert_called_with(key, value) 
        store.store.expireat.assert_called_with(key, 
                                                int(datetime.now().timestamp()) + expir) 
        self.assertEqual(value, store.get(key), (key, value))  
        store.store.get.assert_called_with(key)         
    
        
if __name__ == "__main__":
    unittest.main()