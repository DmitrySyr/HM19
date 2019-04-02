import unittest
import functools
import subprocess
import time
import json

from unittest.mock import patch
from datetime import datetime
from subprocess import Popen, PIPE

from server.store import Store


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


class TestStoreWithMock(unittest.TestCase):
    
    @patch('redis.Redis', autospec=True)
    @cases([
            ('value', 1),             
            ])
    def test_connection_counts(self, _, key, value):        
        store = Store()
        store.store.set.side_effect = [Exception() for i in range(6)]  
        with self.assertRaises(Exception):
            store.set(key, value) 
        self.assertEqual(store.store.set.call_count, 6)
        
    @patch('redis.Redis', autospec=True)
    @cases([
            ('value', 1),             
            ])
    def test_check_set_get_exceptions(self, _, key, value):        
        store = Store()
        store.store.set.side_effect = [Exception() for i in range(6)]  
        store.store.get.side_effect = [Exception() for i in range(6)] 
        
        with self.assertRaises(Exception):
            store.set(key, value) 
        with self.assertRaises(Exception):
            store.get(value)   
            
    @patch('redis.Redis', autospec=True)
    @cases([
            ('value', 1),             
            ])
    def test_check_cache_set__cache_get_noexceptions(self, _, key, value):        
        store = Store()
        store.store.set.side_effect = [Exception() for i in range(6)]  
        store.store.get.side_effect = [Exception() for i in range(6)] 
        
        store.cache_set(key, value) 
        res = store.cache_get(value) 
        self.assertTrue(res is None)
        
    
    @patch('redis.Redis', autospec=True)
    @cases([
            ('value', 1), 
            ('score', 15), 
            ('interests', "['swimming, 'jogging']"),
            ('empty_expire', 90),
            ])
    def test_store_methods_set_get(self, _, key, value):
        store = Store()
        store.store.set.return_value = None
        store.store.get.return_value = value
        store.set(key, value)
        store.store.set.assert_called_with(key, value) 
        res = store.get(key)
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
        store.store.set.return_value = None
        store.store.get.return_value = value
        store.cache_set(key, value, expir)
        store.store.set.assert_called_with('cash_' + key, value) 
        store.store.expireat.assert_called_with('cash_' + key, 
                                                int(datetime.now().timestamp()) + expir) 
        _ = store.cache_get(key)
        store.store.get.assert_called_with('cash_' + key)
        
    
    @patch('redis.Redis', autospec=True)
    @cases([
            ('value', 1), 
            ('score', 15), 
            ('interests', "['swimming, 'jogging']"),
            ('empty_expire', 90),
            ])
    def test_store_methods_set_get_with_repetitions(self, _, key, value):
        side_effect = [Exception() for i in range(5)]
        side_effect.append(value)
        store = Store()
        store.store.set.return_value = None
        store.store.get.side_effect = side_effect
        store.set(key, value)
        store.store.set.assert_called_with(key, value)         
        _ = store.get(key)
        store.store.get.assert_called_with(key)  
        
        
if __name__ == "__main__":
    unittest.main()