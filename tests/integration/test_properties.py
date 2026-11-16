import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_property

VALID = {"name": "Sea View", "channel": "airbnb", "external_listing_id": "abc-1"}


def test_create_returns_201_with_generated_fields(client: TestClient) -> None:
    response = client.post("/properties", json=VALID)

    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["id"])
    assert body["name"] == "Sea View"
    assert body["channel"] == "airbnb"
    assert body["external_listing_id"] == "abc-1"
    assert body["created_at"].endswith(("Z", "+00:00"))


def test_create_strips_surrounding_whitespace(client: TestClient) -> None:
    created = make_property(client, name="  Sea View  ", external_listing_id=" abc-1 ")

    assert created["name"] == "Sea View"
    assert created["external_listing_id"] == "abc-1"


@pytest.mark.parametrize(
    "payload",
    [
        {**VALID, "name": ""},
        {**VALID, "name": "   "},
        {**VALID, "name": "x" * 201},
        {**VALID, "external_listing_id": "  "},
        {**VALID, "external_listing_id": "x" * 101},
        {**VALID, "channel": "expedia"},
        {"name": "No channel", "external_listing_id": "abc-1"},
        {**VALID, "unexpected": "field"},
    ],
)
def test_create_rejects_invalid_payload_with_422(
    client: TestClient, payload: dict[str, Any]
) -> None:
    response = client.post("/properties", json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_create_accepts_values_at_the_length_caps(client: TestClient) -> None:
    response = client.post(
        "/properties", json={**VALID, "name": "n" * 200, "external_listing_id": "i" * 100}
    )

    assert response.status_code == 201


def test_get_returns_the_property(client: TestClient) -> None:
    created = make_property(client)

    response = client.get(f"/properties/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_property_returns_404(client: TestClient) -> None:
    response = client.get(f"/properties/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["code"] == "PROPERTY_NOT_FOUND"


def test_get_malformed_id_returns_422(client: TestClient) -> None:
    assert client.get("/properties/not-a-uuid").status_code == 422


def test_list_is_empty_when_nothing_exists(client: TestClient) -> None:
    response = client.get("/properties")

    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_newest_first(client: TestClient) -> None:
    for index in range(4):
        make_property(client, external_listing_id=f"listing-{index}")

    items = client.get("/properties").json()

    assert len(items) == 4
    created_at = [item["created_at"] for item in items]
    assert created_at == sorted(created_at, reverse=True)


def test_list_filters_by_channel(client: TestClient) -> None:
    airbnb = make_property(client, channel="airbnb")
    make_property(client, channel="direct")
    make_property(client, channel="booking_dot_com")

    items = client.get("/properties", params={"channel": "airbnb"}).json()

    assert [item["id"] for item in items] == [airbnb["id"]]


def test_list_rejects_unknown_channel_with_422(client: TestClient) -> None:
    assert client.get("/properties", params={"channel": "expedia"}).status_code == 422


def test_pages_concatenate_to_the_full_list_without_overlap(client: TestClient) -> None:
    for index in range(5):
        make_property(client, external_listing_id=f"listing-{index}")

    everything = [item["id"] for item in client.get("/properties").json()]
    first = client.get("/properties", params={"skip": 0, "limit": 2}).json()
    second = client.get("/properties", params={"skip": 2, "limit": 2}).json()
    third = client.get("/properties", params={"skip": 4, "limit": 2}).json()

    assert [item["id"] for item in first + second + third] == everything
    assert [len(first), len(second), len(third)] == [2, 2, 1]


def test_skip_past_the_end_returns_empty_list(client: TestClient) -> None:
    make_property(client)

    assert client.get("/properties", params={"skip": 10}).json() == []


@pytest.mark.parametrize(
    "params", [{"skip": -1}, {"limit": 0}, {"limit": 101}, {"limit": "abc"}, {"skip": "x"}]
)
def test_list_rejects_out_of_range_pagination_with_422(
    client: TestClient, params: dict[str, Any]
) -> None:
    assert client.get("/properties", params=params).status_code == 422


def test_limit_of_100_is_accepted(client: TestClient) -> None:
    assert client.get("/properties", params={"limit": 100}).status_code == 200
