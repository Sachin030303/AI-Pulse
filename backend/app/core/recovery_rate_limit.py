"""In-process rate limits for local AI-Pulse development.

Production deployments need shared storage such as Redis.
"""

from collections import deque
from threading import Lock
from time import monotonic


WINDOW_SECONDS = 900
MAX_KEYS = 10000

_lock = Lock()
_requests: dict[str, deque[float]] = {}


def allow_attempt(key: str, *, limit: int) -> bool:
    if not key or limit < 1:
        raise ValueError("Invalid rate limit arguments")

    now = monotonic()

    with _lock:
        if key not in _requests and len(_requests) >= MAX_KEYS:
            for old_key, bucket in list(_requests.items()):
                while bucket and now - bucket[0] >= WINDOW_SECONDS:
                    bucket.popleft()

                if not bucket:
                    del _requests[old_key]

            if len(_requests) >= MAX_KEYS:
                return False

        bucket = _requests.setdefault(key, deque())

        while bucket and now - bucket[0] >= WINDOW_SECONDS:
            bucket.popleft()

        if len(bucket) >= limit:
            return False

        bucket.append(now)
        return True
