from datetime import datetime
import redis
import time


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
                    time.sleep(pow(2, self.attemps - attemps) + 1)
                    attemps -= 1

            return func(*args, **kwargs)
        return helper

    def set(self, key, value, expire=None):
        self.multy_calls(self.store.append)(key, value)
        if expire:
            self.multy_calls(self.store.expireat)(key, int(datetime.now().timestamp()) + expire)

    def get(self, key):
        return self.multy_calls(self.store.get)(key)

    def cache_set(self, key, value, expire=None):
        self.set(key, value, expire)

    def cache_get(self, key):
        return self.get(key)