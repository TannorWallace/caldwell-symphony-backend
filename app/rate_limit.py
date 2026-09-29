"""Simple in-memory rate limiter. Fine for a single Render instance."""

import time
from collections import defaultdict

from fastapi import Request

from .exceptions import TooManyRequestsException

_hits: dict[str, list[float]] = defaultdict(list)


def rate_limit(request: Request, *, key: str, max_hits: int, window_sec: int) -> None:
    ip = request.client.host if request.client else "unknown"
    bucket = f"{key}:{ip}"
    now = time.time()
    recent = [t for t in _hits[bucket] if now - t < window_sec]
    if len(recent) >= max_hits:
        _hits[bucket] = recent
        raise TooManyRequestsException(
            "Too many attempts. Please wait a minute and try again."
        )
    recent.append(now)
    _hits[bucket] = recent