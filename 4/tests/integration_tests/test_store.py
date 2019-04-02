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
    
    
class TestStoreWithoutRedis(unittest.TestCase):
    
    def setUp(self):
        self.store = Store(host='127.0.0.1', port=6380, db=0, socket_timeout=10)     
   
    def test_store_connection_test(self):
        with self.assertRaises(Exception):  
            res = self.store.store.ping()
            
    
class TestStoreWithRedis(unittest.TestCase):
    
    redis_process = None
    PORT = 6380
            
    @classmethod
    def setUpClass(cls):
        print(f"Creating redis instance on port {cls.PORT}")
        cls.redis_process = subprocess.Popen(['redis-server', '--port', str(cls.PORT)])
        time.sleep(0.1)
        #cls.redis_cli = subprocess.Popen(['redis-cli'])         
        cls.store = Store(host='127.0.0.1', port=cls.PORT, db=0, socket_timeout=10) 

    @classmethod
    def tearDownClass(cls):
        print(f"Terminating redis instance on port {cls.PORT}")
        cls.redis_process.terminate()
        cls.redis_process.wait() 
        #cls.redis_cli.terminate()
        #cls.redis_cli.wait()
        print('Redis terminated')
        time.sleep(0.1)     
        
    def test_store_connection(self):
        self.assertTrue(self.store.store.ping())
        
### ----------------  set|get methods -----------------------
        
    @cases([
        ('a', 1),
        ('b', -1),
        ('aa', 2.5),
        ('bb', -5.6788),        
        ])
    def test_set_int_float(self, key, value):
        self.store.set(key, value)
        type_ = type(value)
        
        with Popen(["redis-cli", "-p", str(self.PORT), "get", key], 
                   stdin=PIPE, stdout=PIPE) as cli:
            output, error = cli.communicate()
            self.assertTrue(output)
            self.assertEqual(value, type_(output.strip()))
            
    @cases([       
        ('aaa', [1, 2, 3]),
        ('bbb', [-100, 90, 'sss']),        
        ])
    def test_set_list(self, key, value):
        coded_value = json.dumps(value)
        self.store.set(key, coded_value)        
        
        with Popen(["redis-cli", "-p", str(self.PORT), "get", key], 
                   stdin=PIPE, stdout=PIPE) as cli:
            output, error = cli.communicate()
            self.assertTrue(output)            
            self.assertEqual(value, json.loads(output.strip()))  
            
    @cases([
        ('a', 1, 2),
        ('b', -1, -10),
        ('aa', 2.5, 9.0),
        ('bb', -5.6788, 12),
        ('aaa', [1, 2, 3], 46),
        ('bbb', [-100, 90, 'sss'], [0]),         
        ])
    def test_set_twice(self, key, value, answ):
        if isinstance(value, list):
            value = json.dumps(value)
            answ = json.dumps(answ)
            
        self.store.set(key, value)
        self.store.set(key, answ)        
        
        with Popen(["redis-cli", "-p", str(self.PORT), "get", key], 
                   stdin=PIPE, stdout=PIPE) as cli:
            output, error = cli.communicate()
            self.assertTrue(output)            
            self.assertEqual(str(answ).encode(), output.strip())
            
    @cases([
        ('a', 1),
        ('b', -1),
        ('aa', 2.5),
        ('bb', -5.6788),    
        ('aaa', [1, 2, 3]),
        ('bbb', [-100, 90, 'sss']),         
        ])
    def test_get(self, key, value):
        type_ = type(value)
        if isinstance(value, list):           
            value = json.dumps(value)   
        elif isinstance(value, (int, float)):
            value = str(value)
        
        with Popen(["redis-cli", "-p", str(self.PORT), "set", key, value], 
                   stdin=PIPE, stdout=PIPE) as cli:
            output, error = cli.communicate()
            self.assertEqual(output.strip(), b"OK")        
       
        self.assertEqual(value, self.store.get(key).decode())    
        
    @cases([
        ('a', 1),
        ('b', -1),
        ('aa', 2.5),
        ('bb', -5.6788),    
        ('aaa', [1, 2, 3]),
        ('bbb', [-100, 90, 'sss']),         
        ])
    def test_set_get_methods(self, key, value):
        type_ = type(value)
        if isinstance(value, list):           
            value = json.dumps(value)   
        elif isinstance(value, (int, float)):
            value = str(value)
            
        self.store.set(key, value)
        self.assertEqual(value, self.store.get(key).decode())           
    
        
### ----------------  cash_set|cash_get methods -----------------------
            
    @cases([ 
        ('сa', 1),
        ('сb', -1),
        ('сaa', 2.5),
        ('сbb', -5.6788),            
        ('сaaa', [1, 2, 3]),
        ('сbbb', [-100, 90, 'sss']),        
        ])
    def test_cash_set_without_expiration(self, key, value):
        if isinstance(value, list):            
            value = json.dumps(value) 
            
        self.store.cache_set(key, value)        
        
        with Popen(["redis-cli", "-p", str(self.PORT), "get", "cash_" + key], 
                   stdin=PIPE, stdout=PIPE) as cli:
            output, error = cli.communicate()
            self.assertTrue(output)            
            self.assertEqual(str(value).encode(), output.strip()) 
            
    @cases([ 
        ('a', 1, 2),
        ('b', -1, -10),
        ('aa', 2.5, 9.0),
        ('bb', -5.6788, 12),
        ('aaa', [1, 2, 3], 46),
        ('bbb', [-100, 90, 'sss'], [0]),         
        ])
    def test_cash_set_twice(self, key, value, answ):
        if isinstance(value, list):            
            value = json.dumps(value) 
            answ = json.dumps(answ)
            
        self.store.cache_set(key, value)  
        self.store.cache_set(key, answ)  
        time.sleep(0.01)
        
        with Popen(["redis-cli", "-p", str(self.PORT), "get", "cash_" + key], 
                   stdin=PIPE, stdout=PIPE) as cli:
            output, error = cli.communicate()
            self.assertTrue(output)            
            self.assertEqual(str(answ).encode(), output.strip())
            
    @cases([ 
        ('ссa', 1),
        ('ссb', -1),
        ('ссaa', 2.5),
        ('ссbb', -5.6788),            
        ('ссaaa', [1, 2, 3]),
        ('ссbbb', [-100, 90, 'sss']),        
        ])
    def test_cash_get_without_expiration(self, key, value):
        if isinstance(value, list):            
            value = json.dumps(value)
        elif isinstance(value, (int, float)):
            value = str(value)   
            
        self.assertEqual(self.store.get("cash_" + key)  , self.store.cache_get(key)) 
        
    @cases([
        ('ea', 1),
        ('eb', -1),
        ('eaa', 2.5),
        ('ebb', -5.6788),
        ('eaaa', [1, 2, 3]),
        ('ebbb', [-100, 90, 'sss']),         
        ])
    def test_cash_set_expired(self, key, value):
        if isinstance(value, list):
            value = json.dumps(value)
            
        self.store.cache_set(key, value, 1)        
        time.sleep(1)
        
        with Popen(["redis-cli", "-p", str(self.PORT), "get", 'cash_' + key], 
                   stdin=PIPE, stdout=PIPE) as cli:
            output, error = cli.communicate()
            self.assertFalse(output.strip())        
            
    @cases([
        ('ea', 1),
        ('eb', -1),
        ('eaa', 2.5),
        ('ebb', -5.6788),
        ('eaaa', [1, 2, 3]),
        ('ebbb', [-100, 90, 'sss']),         
        ])
    def test_cash_get_expired(self, key, value):
        type_ = type(value)
        if isinstance(value, list):            
            value = json.dumps(value)   
        elif isinstance(value, (int, float)):
            value = str(value)
        
        with Popen(["redis-cli", "-p", str(self.PORT), "set", 'cash_' + key, 
                    value, 'EX', '1'], stdin=PIPE, stdout=PIPE) as cli:
            output, error = cli.communicate()
            self.assertEqual(output.strip(), b"OK") 
            
        time.sleep(1)
       
        self.assertFalse(self.store.cache_get(key))  
        

class TestStoreReconnection(unittest.TestCase):
    
    PORT = 6380
    
    @classmethod
    def setUpClass(cls):
        print(f"Creating redis instance on port {cls.PORT}")
        cls.redis_process = subprocess.Popen(['redis-server', '--port', str(cls.PORT)])
        time.sleep(0.1)        

    @classmethod
    def tearDownClass(cls):
        print(f"Terminating redis instance on port {cls.PORT}")
        cls.redis_process.terminate()
        cls.redis_process.wait()         
        print('Redis terminated')
        time.sleep(0.1)        
    
    def exec_set(self, key, value):
        store = Store(host='127.0.0.1', port=self.PORT, db=0, socket_timeout=10) 
        store.set(key, value)
    
    def exec_get(self, key):
        store = Store(host='127.0.0.1', port=self.PORT, db=0, socket_timeout=10) 
        return store.get(key)  
    
    @cases([
        ('ea', 1),
        ('eb', -1),
        ('eaa', 2.5),
        ('ebb', -5.6788),
        ('eaaa', [1, 2, 3]),
        ('ebbb', [-100, 90, 'sss']),         
        ])    
    def test_reconnection(self, key, value):
        type_ = type(value)
        if isinstance(value, list):            
            value = json.dumps(value)   
        elif isinstance(value, (int, float)):
            value = str(value)        
            
        self.exec_set(key, value)
        res = self.exec_get(key)         
        self.assertEqual(value, res.decode())           
        
        
if __name__ == "__main__":
    unittest.main()