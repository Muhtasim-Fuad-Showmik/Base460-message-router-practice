from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from message_router.main import create_app


@pytest.fixture
def app(tmp_path: Path) -> FastAPI:
    """A fresh app on its own SQLite file, so every test is isolated."""
    return create_app(f"sqlite:///{tmp_path / 'test.db'}")


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:  # the context manager runs the lifespan
        yield test_client
