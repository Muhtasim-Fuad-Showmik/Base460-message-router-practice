from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from message_router.main import create_app


@pytest.fixture
def app(tmp_path: Path) -> FastAPI:
    """A fresh app on its own SQLite file, so every test is isolated."""
    return create_app(f"sqlite:///{tmp_path / 'test.db'}")


def make_property(client: TestClient, **overrides: Any) -> dict[str, Any]:
    """Create a property through the API (so validation is exercised) and return its JSON."""
    payload = {
        "name": "Sea View Apartment",
        "channel": "airbnb",
        "external_listing_id": "listing-001",
        **overrides,
    }
    response = client.post("/properties", json=payload)
    assert response.status_code == 201, response.text
    return response.json()  # type: ignore[no-any-return]


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:  # the context manager runs the lifespan
        yield test_client
