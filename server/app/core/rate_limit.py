"""Простий rate limiting (ковзне вікно, у памʼяті процесу) для REST і WebSocket."""

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request

from app.core.config import settings
from app.core.errors import RateLimitError


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window: float) -> tuple[bool, int]:
        """Повертає (дозволено, через скільки секунд можна повторити)."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= window:
                hits.popleft()
            if len(hits) >= limit:
                return False, max(1, int(window - (now - hits[0])) + 1)
            hits.append(now)
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limit(times: int, seconds: int, scope: str) -> Callable[[Request], None]:
    """Створює залежність FastAPI: не більше `times` запитів за `seconds` з однієї IP."""

    def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        allowed, retry_after = limiter.check(f"{scope}:{client_ip(request)}", times, seconds)
        if not allowed:
            raise RateLimitError(headers={"Retry-After": str(retry_after)})

    return dependency
