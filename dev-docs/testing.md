# Testing

Behaviour-first: assert what the API or function does, never how it is wired.

## Tools

`pytest` + `httpx`-backed `fastapi.testclient.TestClient`. No mocking of the repository/service layers in
integration tests — use a real in-memory SQLite.

## Fixtures (`tests/conftest.py`)

- `engine`: `sqlite://` (in-memory) with `StaticPool` + `check_same_thread=False`, tables created per test (function scope =
  isolated, fast enough here).
- `client`: `TestClient(app)` with `get_db` overridden to the test session factory.
- `fixed_clock`: patches `app.core.clock.utcnow` to a constant.
- Builders: `make_property(client, **overrides)` and `make_message(client, property_id, **overrides)` that go
  through the API, so tests exercise real validation. Defaults live in one place.

## What to cover

Unit (`tests/unit`, no DB):
- `classify(content)`: one case per intent; case-insensitivity; multi-category → first in the specified order;
  no match → `other`; the multi-word keywords (`check-in`, `not working`); whole-word behaviour is pinned (variants: `towels`, `fixed`, `leaking`, `check in`, `not  working`, `key`, `amenity`, `cancelled`, `wi-fi` match; `arrive` does not): `nearly`, `template`,
  `prefix` do NOT match `early`, `late`, `fix`; `Late!` and `not  working`-style punctuation/case still match.
- Status transition table: every allowed and every forbidden (from, action) pair.

Integration (`tests/integration`):
- Properties: create 201, get 200/404, list filter by channel, pagination bounds, invalid enum 422.
- Messages: create 201 with `status=pending` and `intent=null`; unknown property 404; bad email 422; content `""`
  and 2001 chars 422, 2000 chars 201; list filters (`property_id`, `status`, `intent`) and pagination; detail
  includes property and responses.
- Classify: sets intent + `classified`; second call 409; unknown id 404.
- Respond: 201, status `responded`; from `pending` allowed; repeat respond allowed (two responses stored); on `escalated` 409; invalid `response_type` 422; `escalation_notice` on `/respond` → 422.
- Concurrency (file-backed temp DB, two threads): simultaneous escalate of one message → exactly one 201, one 409, one stored response.
- Input: whitespace-only `content`/`guest_name`/`name`/`body` → 422; surrounding whitespace is stripped; over-cap lengths → 422.
- Escalate: from `pending`/`classified`/`responded` OK; second escalate 409; creates `escalation_notice` with default body, status `escalated`.
- Every error response matches the problem+json shape.

## Rules

- One behaviour per test, named `test_<action>_<condition>_<expected>`.
- No sleeping, no real clock, no ordering dependence between tests.
- Plain `assert` with explicit expected values; no snapshot of whole payloads unless the payload is the contract.
- A bug fix starts with a failing test.
