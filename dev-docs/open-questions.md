# Decision log

Decisions are binding; `api-conventions.md`, `architecture.md` and `testing.md` agree with them.

## Decided

| # | Topic | Decision |
|---|---|---|
| 1 | Sync vs async | **Sync** SQLAlchemy 2.0 (`Session`, stdlib `sqlite3`). No external I/O in scope. Relations a response needs are eager-loaded in the repository (`selectinload`/`joinedload`). |
| 2 | 400 vs 422 | **422 only** for every validation failure (problem+json). 400 is unused; the README says so. |
| 3 | Classification matching | Case-insensitive **whole-word** matching with controlled variants — see "Classification matching". |
| 4 | State transitions | Transition table below, enforced by one atomic status-guarded update (no read-then-check). |
| 5 | respond/escalate result | The created `AutomatedResponse`, 201. |
| 6 | Escalation body | Fixed module constant in the service. |
| 7 | Lists | Plain JSON array; `skip` default 0 (>=0), `limit` default 50 (1..100); order `created_at DESC, id`. |
| 8 | `GET /messages/{id}` | Nested `property` + `responses` (ordered by `created_at`), eager-loaded. |
| 9 | Uniqueness | No `(channel, external_listing_id)` constraint — not in the spec. |
| 10 | Input strictness | Strip surrounding whitespace, then reject blanks (422) for `guest_name`, `content`, `name`, `external_listing_id`, response `body`. Caps: `name` 200, `external_listing_id` 100, `guest_name` 200, `content` 2000, `body` 2000. |
| 11 | `/respond` type | Request accepts only `ai_generated` / `template`; `escalation_notice` is 422 and is created only by `/escalate`. |
| 12 | Database | SQLite, sync; file `message_router.db`, override with `DATABASE_URL`; `create_all` in the app lifespan; `PRAGMA foreign_keys=ON`; busy timeout set. No Alembic. |
| 13 | Timestamps | Stored UTC, returned timezone-aware (a small `UtcDateTime` `TypeDecorator`, since SQLite drops tzinfo). |
| 14 | Delivery | Local only. README: setup, run, test commands (plus the 422-only note). |
| 15 | Commits | One conventional commit per slice, no ticket bracket. |
| 16 | Bonus order | Core first. Then 1) `GET /properties/{id}/messages` summary, 2) rate limit. Classifier unit tests are core. |
| 17 | Property message summary | `GET /properties/{id}/messages` returns `{summary, messages}`: counts over all of the property's messages (one grouped query) plus the usual paginated, newest-first page. |
| 18 | Rate limit | At most 10 `POST /messages` per property per rolling minute (`core/config.py`). In-memory sliding window, thread-safe, injected clock; over the limit is 429 `RATE_LIMIT_EXCEEDED` with `Retry-After` (whole seconds, rounded up). Checked after validation and the property-exists check, so 404/422 requests do not use quota; blocked attempts are not recorded. Per-process state: not shared between workers. |

### Transition table

| Action | pending | classified | responded | escalated |
|---|---|---|---|---|
| classify | → classified | 409 | 409 | 409 |
| respond | → responded | → responded | stays responded (repeat allowed, append-only) | 409 |
| escalate | → escalated | → escalated | → escalated | 409 |

- Respond does not require classification first; such a message may end `responded` with `intent = null`.
- `intent` is only ever set by `classify`.
- A malformed UUID is 422; a well-formed unknown `property_id` on message creation is 404.

### Concurrency guard

Each transition is one conditional update driven by the table, never read-then-check:

```sql
UPDATE guest_messages SET status = :new [, intent = :intent]
WHERE id = :id AND status IN (:allowed_from)
```

`rowcount == 1` → insert the response (if any) and commit once. `rowcount == 0` → one `exists` check: missing → 404,
otherwise → 409. Allowed-from: classify `{pending}`; respond and escalate `{pending, classified, responded}` (escalate
excludes `escalated`; respond excludes `escalated`).

### Classification matching

- `\b` boundaries, case-insensitive: `early` does not match "nearly", `late` not "template"/"plate", `fix` not "prefix".
- Multi-word or hyphenated keywords join their tokens with `[\s-]+`: `check-in`, `check in`, `not working`,
  `not  working`. `checkin` is its own listed keyword.
- Optional inflection suffix `(?:s|es|ed|ing)?` on the last token (`towels`, `fixed`, `leaking`, `bookings`); the whole
  word must still end there, so "earlier" and "fixture" do not match.
- Extra table entries where a suffix cannot derive the form: `key`, `amenity`, `cancelled`, `wi-fi`.
- First category in the spec's order wins; no match → `other`.
- No stemming beyond this (e.g. "arrive" does not match `arrival`); pinned in tests.

## Still open

Nothing.
