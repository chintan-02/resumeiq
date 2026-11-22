"""Per-client request limits for the public API.

Who is the client? On Cloud Run the Google front end appends the address it saw as
the last entry of X-Forwarded-For; anything a caller sends ends up to the left of
it. So the trusted address is the entry `TRUSTED_HOPS` from the right (1 = the
last), and spoofing the header cannot change it. With a load balancer in front, set
RESUMEIQ_TRUSTED_HOPS=2.

The website's backend calls this API from Vercel's servers, so all site traffic
arrives from a few Vercel addresses. Per-visitor limits therefore live in the site
(apps/web/src/lib/proxy.ts); these limits stop direct abuse and are set high enough
that site traffic does not reach them. Limits are per instance (max 2), in memory,
and addresses are only held as hashes.
"""

from __future__ import annotations

import hashlib
import math
import os
import time
from collections import deque
from threading import Lock

DEFAULT_LIMITS = {"fit-map": 60, "upload": 30, "rewrite": 20, "check": 60}


def parse_limits(raw: str | None) -> dict[str, int]:
    """RESUMEIQ_RATE_LIMITS="fit-map=60,upload=30"; unknown names and bad values are ignored."""
    limits = dict(DEFAULT_LIMITS)
    for part in (raw or "").split(","):
        name, _, value = part.partition("=")
        if name.strip() in limits and value.strip().isdigit():
            limits[name.strip()] = int(value)
    return limits


def client_key(forwarded_for: str | None, peer: str | None, trusted_hops: int = 1) -> str:
    entries = [e.strip() for e in (forwarded_for or "").split(",") if e.strip()]
    address = entries[-trusted_hops] if len(entries) >= trusted_hops else (peer or "unknown")
    return hashlib.sha256(address.encode()).hexdigest()[:16]


class RateLimiter:
    """Sliding one-minute window per (bucket, client)."""

    def __init__(self, limits: dict[str, int], window: float = 60.0, max_keys: int = 10_000) -> None:
        self.limits = limits
        self.window = window
        self.max_keys = max_keys
        self._hits: dict[tuple[str, str], deque[float]] = {}
        self._lock = Lock()

    def check(self, bucket: str, key: str, now: float | None = None) -> tuple[bool, int, int]:
        """(allowed, remaining, retry_after_seconds)."""
        limit = self.limits[bucket]
        now = time.monotonic() if now is None else now
        with self._lock:
            if len(self._hits) > self.max_keys:
                self._hits.clear()  # bounded memory; at worst a brief reset of counts
            hits = self._hits.setdefault((bucket, key), deque())
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= limit:
                return False, 0, max(1, math.ceil(self.window - (now - hits[0])))
            hits.append(now)
            return True, limit - len(hits), 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def from_env() -> tuple[RateLimiter, int]:
    hops = os.environ.get("RESUMEIQ_TRUSTED_HOPS", "1")
    return RateLimiter(parse_limits(os.environ.get("RESUMEIQ_RATE_LIMITS"))), max(1, int(hops) if hops.isdigit() else 1)
