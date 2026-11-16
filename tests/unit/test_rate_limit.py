import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest

from message_router.core.rate_limit import SlidingWindowRateLimiter
from tests.fakes import FakeClock


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def limiter(clock: FakeClock) -> SlidingWindowRateLimiter:
    return SlidingWindowRateLimiter(limit=3, window=timedelta(seconds=60), clock=clock)


def test_allows_up_to_the_limit(limiter: SlidingWindowRateLimiter) -> None:
    assert [limiter.acquire("p") for _ in range(3)] == [None, None, None]


def test_blocks_the_request_over_the_limit_with_the_wait_time(
    limiter: SlidingWindowRateLimiter, clock: FakeClock
) -> None:
    for _ in range(3):
        limiter.acquire("p")
    clock.advance(seconds=20)

    retry_after = limiter.acquire("p")

    assert retry_after == timedelta(seconds=40)  # the oldest hit leaves the window at t+60


def test_blocked_requests_do_not_extend_the_block(
    limiter: SlidingWindowRateLimiter, clock: FakeClock
) -> None:
    for _ in range(3):
        limiter.acquire("p")
    for _ in range(5):
        assert limiter.acquire("p") is not None

    clock.advance(seconds=60)

    assert limiter.acquire("p") is None


def test_window_slides_one_hit_at_a_time(
    limiter: SlidingWindowRateLimiter, clock: FakeClock
) -> None:
    limiter.acquire("p")  # t=0
    clock.advance(seconds=30)
    limiter.acquire("p")  # t=30
    limiter.acquire("p")  # t=30
    assert limiter.acquire("p") is not None

    clock.advance(seconds=30)  # t=60: the t=0 hit expired, the two t=30 hits remain

    assert limiter.acquire("p") is None
    assert limiter.acquire("p") is not None


def test_hits_exactly_one_window_old_no_longer_count(
    limiter: SlidingWindowRateLimiter, clock: FakeClock
) -> None:
    for _ in range(3):
        limiter.acquire("p")
    clock.advance(seconds=60)

    assert limiter.acquire("p") is None


def test_keys_are_limited_independently(limiter: SlidingWindowRateLimiter) -> None:
    for _ in range(3):
        limiter.acquire("a")

    assert limiter.acquire("a") is not None
    assert limiter.acquire("b") is None


def test_idle_keys_are_forgotten(limiter: SlidingWindowRateLimiter, clock: FakeClock) -> None:
    limiter.acquire("a")
    clock.advance(seconds=61)

    limiter.acquire("b")

    assert limiter.tracked_keys == 1


def test_concurrent_callers_never_exceed_the_limit() -> None:
    limiter = SlidingWindowRateLimiter(limit=10, window=timedelta(seconds=60), clock=FakeClock())
    barrier = threading.Barrier(40)

    def attempt() -> bool:
        barrier.wait()
        return limiter.acquire("p") is None

    with ThreadPoolExecutor(max_workers=40) as pool:
        allowed = [future.result() for future in [pool.submit(attempt) for _ in range(40)]]

    assert sum(allowed) == 10


@pytest.mark.parametrize(("limit", "window"), [(0, 60), (-1, 60), (5, 0), (5, -1)])
def test_rejects_a_non_positive_configuration(limit: int, window: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        SlidingWindowRateLimiter(limit=limit, window=timedelta(seconds=window))
