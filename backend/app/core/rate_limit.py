"""Tiny in-process token-bucket limiter.

Good enough for a single Render instance; swap the store for Redis when scaling horizontally
(the interface stays the same).
"""
import threading
import time

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, capacity: int, refill_per_sec: float):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            tokens, last = self._buckets.get(key, (float(self.capacity), now))
            tokens = min(self.capacity, tokens + (now - last) * self.refill_per_sec)
            if tokens < 1:
                self._buckets[key] = (tokens, now)
                return False
            self._buckets[key] = (tokens - 1, now)
            if len(self._buckets) > 50_000:  # crude memory guard
                self._buckets.clear()
            return True

    def check(self, key: str) -> None:
        if not self.allow(key):
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Slow down a little! Try again shortly.")


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


guest_limiter = RateLimiter(capacity=5, refill_per_sec=5 / 3600)  # 5 new learners / hour / IP
answer_limiter = RateLimiter(capacity=60, refill_per_sec=2)
tutor_limiter = RateLimiter(capacity=6, refill_per_sec=1 / 10)  # bursts of 6, then 1 every 10s
