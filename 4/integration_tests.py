



import hashlib

import datetime

import json
import unittest
import random
import functools
import time
import redis
import os
import signal
import subprocess

import http.client

from api import MainHTTPHandler, ADMIN_LOGIN
from store import Store

import api

def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator

class TestApi(unittest.TestCase):
    
    redis = None
    redis_process = None
    PORT = 6379
    
    http_server = None
    http_server_process = None
    HTTP_SERVER_PORT = 8080
    
    conn = None
        
    @classmethod
    def setUpClass(cls):
        print (f"Creating redis instance on port {cls.PORT}")
        cls.redis_process = subprocess.Popen(['redis-server', '--port', str(cls.PORT)])
        time.sleep(0.1)
        cls.store = Store(port=cls.PORT)  
        interests = ("cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus")
        for i in [0, 1, 2, 3]:
            cls.store.set(f'i:{i}', json.dumps(random.sample(interests, 2)), 60)        
        
        print(f'Running http server on port {cls.HTTP_SERVER_PORT}')
        server_path = os.path.join(os.getcwd(), 'api.py')
        cls.http_server_process = subprocess.Popen(['python', server_path, '-p', 
                                                    str(cls.HTTP_SERVER_PORT)])
        time.sleep(0.1)
        
        print(f'Running http client on port {cls.HTTP_SERVER_PORT}')
        cls.conn = http.client.HTTPConnection('127.0.0.1', 
                                               cls.HTTP_SERVER_PORT, timeout=25)

    @classmethod
    def tearDownClass(cls):
        print (f"Terminating redis instance on port {cls.PORT}")
        cls.redis_process.terminate()
        cls.redis_process.wait()  
        print('Redis terminated')
        time.sleep(0.1)
        cls.conn.close()  
        print('Connection closed.')
        time.sleep(0.1)
        print (f"Terminating http server instance on port {cls.HTTP_SERVER_PORT}")
        cls.http_server_process.terminate()
        cls.http_server_process.wait()
        print('HTTP server terminated')
         
        
    def get_response(self, request):
        self.conn.request('POST', '/method', body=json.dumps(request))
        resp = self.conn.getresponse()
        if resp.status == 200:
            data = json.loads(resp.read())
            return data.get('response'), data.get('code') 
        else:
            print(resp.status, resp.code)
            return None, resp.code
    
    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            string_to_encode = datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT
            request["token"] = hashlib.sha512(string_to_encode.encode()).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(msg.encode()).hexdigest()  
            
    def get_interests(self, cid):
        r = self.store.get("i:%s" % cid)
        return json.loads(r) if r else []    
    
    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, 
         "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
    ])     
    def test_good_score_request_no_admin(self, arg):  
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score",
                   "arguments": arg}
        self.set_valid_auth(request)
        resp, code = self.get_response(request)
        if resp:
            score = resp.get('score')             
            self.assertEqual(code, 200)
            self.assertTrue(score in [0.5, 1.5, 2.0, 3.0, 3.5, 4.5, 5.0])
            
    def test_good_score_request_admin(self): 
        arg = {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, 
               "birthday": "01.01.2000", "first_name": "a", "last_name": "b"}
        request = {"account": "horns&hoofs", "login": ADMIN_LOGIN, "method": 
                   "online_score", "arguments": arg}
        self.set_valid_auth(request)
        resp, code = self.get_response(request)
        if resp:
            score = resp.get('score')             
            self.assertEqual(code, 200)
            self.assertTrue(score == 42)   
            
    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_good_interests_request(self, arg):  
        request = {"account": "horns&hoofs", "login": 'not_admin', 
                   "method": "clients_interests", "arguments": arg}        
        
        self.set_valid_auth(request)
        resp, code = self.get_response(request)
        if resp:
            self.assertEqual(code, 200)
            for k, v in resp.items():
                test_value = self.get_interests(k)
                self.assertEqual(v, test_value)
                
if __name__ == "__main__":
    unittest.main()