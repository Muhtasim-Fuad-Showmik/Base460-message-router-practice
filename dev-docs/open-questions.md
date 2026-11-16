# Decisions and remaining questions

Decisions are binding for planning and code; `api-conventions.md` and `testing.md` agree with them.

## Decided

| # | Topic | Decision |
|---|---|---|
| 1 | Sync vs async | **Sync** SQLAlchemy 2.0 (`Session`, stdlib `sqlite3`). Nothing in the brief needs async (no external I/O); sync is simpler to write and test. Relations a response needs are still eager-loaded in the repository (`selectinload`/`joinedload`) to avoid N+1. |
| 2 | 400 vs 422 | **422 only** for every Pydantic/validation failure (problem+json shape). 400 is not used; say so in the README. |
| 3 | Classification matching | **Case-insensitive whole-word / whole-phrase** match (`\b` boundaries), first category in the spec's order wins. `early` does not match "nearly", `late` does not match "template". Multi-word keywords (`not working`) match as phrases; `check-in` and `checkin` are separate keywords as listed. |
| 4 | State transitions | See table below. |
| 5 | Response to respond/escalate | The created `AutomatedResponse`, 201. |
| 6 | Escalation body | Fixed module constant in the service. |
| 7 | List ordering | `created_at DESC, id`. |
| 8 | `GET /messages/{id}` | Nested `property` + `responses` (ordered by `created_at`), eager-loaded. |
| 9 | Unique `(channel, external_listing_id)` | Not in spec — not added. |

### Transition table

| Action | pending | classified | responded | escalated |
|---|---|---|---|---|
| classify | → classified | 409 | 409 | 409 |
| respond | → responded | → responded | stays responded (repeat allowed, append-only) | 409 |
| escalate | → escalated | → escalated | → escalated | 409 |

- Respond does not require classification first (no 409 from `pending`); such a message may end `responded` with
  `intent = null`, because classify is then a 409. Accepted.
- `intent` is only ever set by `classify`.
- A malformed UUID is a 422; a well-formed but unknown `property_id` on message creation is a 404.

## Still open

| # | Question | Leaning |
|---|---|---|
| A | Bonus order if time remains | 1) classifier unit tests (do anyway), 2) `/properties/{id}/messages` summary, 3) rate limit |
| B | Rate limit (if built): in-memory sliding window per `property_id` as a dependency; response 429 + `Retry-After` | Decide only if reached |
