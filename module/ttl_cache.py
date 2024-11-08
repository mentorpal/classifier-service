import time


class TTLCache:
    def __init__(self, ttl=300):
        self.ttl = ttl
        self.cache = {}

    def get(self, key):
        if key not in self.cache:
            return None
        if self.cache[key]["expires"] < time.time():
            del self.cache[key]
            return None
        return self.cache[key]["value"]

    def set(self, key, value):
        self.cache[key] = {"value": value, "expires": time.time() + self.ttl}
