from datetime import datetime
import redis
import time
import logging


class Store(object):
    def __init__(self, *args, **kwargs):
        self.store = redis.Redis(*args, **kwargs)
        self.attemps = 5

    def multy_calls(self, func):
        def helper(*args, **kwargs):
            attemps = self.attemps            

            while attemps > 0:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    time.sleep(self.attemps - attemps + 1)
                    attemps -= 1

            return func(*args, **kwargs)
        return helper

    def set(self, key, value, expire=None):
        try:
            self.multy_calls(self.store.append)(key, value)
            if expire:
                self.multy_calls(self.store.expireat)(key, 
                                                      int(datetime.now().timestamp()) 
                                                      + expire)
        except Exception as e:
            logging.error(repr(e))

    def get(self, key):
        try:
            res = self.multy_calls(self.store.get)(key)
        except Exception as e:
            logging.error(repr(e))
            res = None
            
        return res

    def cache_set(self, key, value, expire=None):
        try:
            self.multy_calls(self.store.append)('cash_' + key, value)
            if expire:
                self.multy_calls(self.store.expireat)('cash_' + key, 
                                                      int(datetime.now().timestamp()) 
                                                      + expire)
        except Exception as e:
            logging.error(repr(e))
            
    def cache_get(self, key):
        try:
            res = self.multy_calls(self.store.get)('cash_' + key)
        except Exception as e:
            logging.error(repr(e))
            res = None
            
        return res