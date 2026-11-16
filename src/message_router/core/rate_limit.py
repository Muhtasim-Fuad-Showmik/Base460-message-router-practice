import threading
from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta

from message_router.core.clock import utcnow


class SlidingWindowRateLimiter:
    """In-memory sliding-window limiter: at most `limit` hits per key within `window`.

    Thread-safe. State lives in this process only, so it is not shared between workers.
    """

    def __init__(
        self, *, limit: int, window: timedelta, clock: Callable[[], datetime] = utcnow
    ) -> None:
        if limit <= 0 or window <= timedelta(0):
            msg = "limit and window must be positive"
            raise ValueError(msg)
        self._limit = limit
        self._window = window
        self._clock = clock
        self._hits: dict[str, deque[datetime]] = {}
        self._lock = threading.Lock()

    @property
    def tracked_keys(self) -> int:
        with self._lock:
            return len(self._hits)

    def acquire(self, key: str) -> timedelta | None:
        """Record a hit for `key`. Returns None if allowed, else how long until a hit is allowed.

        Blocked attempts are not recorded, so they never extend the block.
        """
        with self._lock:
            now = self._clock()
            self._forget_expired(now)
            hits = self._hits.setdefault(key, deque())
            if len(hits) >= self._limit:
                return hits[0] + self._window - now
            hits.append(now)
            return None

    def _forget_expired(self, now: datetime) -> None:
        cutoff = now - self._window
        for key in list(self._hits):
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if not hits:
                del self._hits[key]
