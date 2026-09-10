import time
from collections import defaultdict, deque
from typing import DefaultDict, Deque

from app.config import settings

try:
    import redis
except Exception:  # pragma: no cover
    redis = None


class RedisRateLimiter:
    def __init__(self, redis_url: str | None = None, limit: int | None = None, window_seconds: int | None = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.limit = limit if limit is not None else settings.RATE_LIMIT_PER_MINUTE
        self.window_seconds = window_seconds if window_seconds is not None else settings.RATE_LIMIT_WINDOW_SECONDS
        self.client = None
        self.memory_store: DefaultDict[str, Deque[float]] = defaultdict(deque)

        if redis is not None and self.redis_url:
            try:
                self.client = redis.Redis.from_url(self.redis_url, decode_responses=True)
                self.client.ping()
            except Exception:
                self.client = None

    def allow_request(self, key: str) -> bool:
        if self.client is not None:
            current = int(self.client.get(key) or 0)
            if current >= self.limit:
                return False
            pipe = self.client.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window_seconds)
            pipe.execute()
            return True

        now = time.time()
        timestamps = self.memory_store[key]
        while timestamps and now - timestamps[0] > self.window_seconds:
            timestamps.popleft()

        if len(timestamps) >= self.limit:
            return False

        timestamps.append(now)
        return True

    def reset(self):
        if self.client is not None:
            try:
                self.client.flushdb()
            except Exception:
                pass
        self.memory_store.clear()


rate_limiter = RedisRateLimiter()
