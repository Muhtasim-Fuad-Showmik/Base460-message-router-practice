import uuid
from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from message_router.core.config import MESSAGE_CREATE_LIMIT, MESSAGE_CREATE_WINDOW
from message_router.core.rate_limit import SlidingWindowRateLimiter
from message_router.main import create_app
from tests.conftest import make_property
from tests.fakes import FakeClock

LIMIT = MESSAGE_CREATE_LIMIT


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def limited_client(tmp_path: Path, clock: FakeClock) -> Iterator[TestClient]:
    limiter = SlidingWindowRateLimiter(limit=LIMIT, window=MESSAGE_CREATE_WINDOW, clock=clock)
    app = create_app(f"sqlite:///{tmp_path / 'limited.db'}", message_rate_limiter=limiter)
    with TestClient(app) as test_client:
        yield test_client


def _create(client: TestClient, property_id: str, **overrides: Any) -> Any:
    payload = {
        "property_id": property_id,
        "guest_name": "Ann",
        "guest_email": "ann@example.com",
        "content": "hello",
        **overrides,
    }
    return client.post("/messages", json=payload)


def test_the_documented_limit_is_ten_per_minute() -> None:
    assert LIMIT == 10
    assert timedelta(minutes=1) == MESSAGE_CREATE_WINDOW


def test_creations_over_the_limit_are_rejected_with_429_and_retry_after(
    limited_client: TestClient,
) -> None:
    property_id = make_property(limited_client)["id"]
    assert all(_create(limited_client, property_id).status_code == 201 for _ in range(LIMIT))

    response = _create(limited_client, property_id)

    assert response.status_code == 429
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["Retry-After"] == "60"
    assert response.json()["code"] == "RATE_LIMIT_EXCEEDED"
    assert response.json()["status"] == 429


def test_rejected_creations_store_nothing(limited_client: TestClient) -> None:
    property_id = make_property(limited_client)["id"]
    for _ in range(LIMIT + 3):
        _create(limited_client, property_id)

    stored = limited_client.get("/messages", params={"property_id": property_id, "limit": 100})

    assert len(stored.json()) == LIMIT


def test_retry_after_shrinks_as_time_passes(limited_client: TestClient, clock: FakeClock) -> None:
    property_id = make_property(limited_client)["id"]
    for _ in range(LIMIT):
        _create(limited_client, property_id)
    clock.advance(seconds=45)

    response = _create(limited_client, property_id)

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "15"


def test_creation_is_allowed_again_once_the_window_has_passed(
    limited_client: TestClient, clock: FakeClock
) -> None:
    property_id = make_property(limited_client)["id"]
    for _ in range(LIMIT):
        _create(limited_client, property_id)
    assert _create(limited_client, property_id).status_code == 429

    clock.advance(seconds=60)

    assert _create(limited_client, property_id).status_code == 201


def test_each_property_has_its_own_limit(limited_client: TestClient) -> None:
    busy = make_property(limited_client, external_listing_id="busy")["id"]
    quiet = make_property(limited_client, external_listing_id="quiet")["id"]
    for _ in range(LIMIT):
        _create(limited_client, busy)

    assert _create(limited_client, busy).status_code == 429
    assert _create(limited_client, quiet).status_code == 201


def test_invalid_and_unknown_property_requests_do_not_use_up_the_quota(
    limited_client: TestClient,
) -> None:
    property_id = make_property(limited_client)["id"]
    for _ in range(LIMIT):
        assert _create(limited_client, property_id, guest_email="nope").status_code == 422
        assert _create(limited_client, str(uuid.uuid4())).status_code == 404

    assert all(_create(limited_client, property_id).status_code == 201 for _ in range(LIMIT))


def test_other_endpoints_are_not_limited(limited_client: TestClient) -> None:
    property_id = make_property(limited_client)["id"]
    message_id = _create(limited_client, property_id).json()["id"]
    for _ in range(LIMIT + 5):
        assert limited_client.get(f"/messages/{message_id}").status_code == 200
        assert limited_client.get("/messages").status_code == 200
