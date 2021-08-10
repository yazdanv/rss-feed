import json

import redis

from app.core.config import settings


class CustomRedis:
    def __init__(self, host=None, port=settings.REDIS_PORT, db=settings.REDIS_DB):
        if host is None:
            host = settings.REDIS_HOST
        self._redis = redis.Redis(host, port, db)

    def get(self, key: str):
        return json.loads(self._redis.get(key))

    def set(self, key: str, data, ttl: int):
        return self._redis.set(key, json.dumps(data), ex=ttl)


def get_redis():
    return CustomRedis()
