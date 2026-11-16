# API conventions

Wins over `patterns/` on any conflict. Requirements come from `ASSIGNMENT.md`.

## Paths and verbs

Exactly the endpoints in the assignment. Plural nouns, no trailing slash, no version prefix (not asked for).
Actions that are not CRUD (`classify`, `respond`, `escalate`) are sub-resource verbs on the message, as specified.

## Status codes

| Case | Code |
|---|---|
| Create property / message / response / escalation | 201 |
| Read, list, classify | 200 |
| Schema violation (bad email, content length, bad enum, bad UUID) | 422 (FastAPI/Pydantic default) |
| Unknown id, unknown `property_id` on message creation | 404 |
| Invalid state transition (classify twice, respond to escalated) | 409 |

The assignment lists both 400 and 422; decided (`open-questions.md`): every validation failure is 422, 400 is unused.

## Error shape (RFC 9457 `application/problem+json`)

```json
{ "type": "about:blank", "title": "Conflict", "status": 409, "detail": "Message is already classified", "code": "MESSAGE_ALREADY_CLASSIFIED" }
```

- One `ErrorCode` enum; each domain exception carries a code and HTTP status.
- Override the default `RequestValidationError` handler so 422s use the same shape (with an `errors` list).
- Never leak stack traces or SQL in `detail`.

## Pagination and filtering

- `?skip=` (default 0, `>=0`) and `?limit=` (default 50, `1..100`) — validated via `Query(ge=, le=)`.
- Every list is bounded and deterministically ordered (`created_at DESC, id`) so pages are stable.
- Filters are optional query params combined with AND; unknown enum values → 422.
- List responses: a plain JSON array (the assignment shows no envelope). Do not add `total` unless planning decides to.

## Schemas

- Naming: `PropertyCreate` / `PropertyRead`; `MessageCreate` / `MessageRead` (list item and classify result) /
  `MessageDetail` (adds `property` and `responses`); `AutomatedResponseCreate` / `AutomatedResponseRead`. Use the
  `Create`/`Read`/`Detail` suffixes everywhere (matches `patterns/schemas.md`).
- Text inputs are stripped, then must be non-empty; caps: `name` 200, `external_listing_id` 100, `guest_name` 200, `content` 2000, response `body` 2000.
- `POST /messages/{id}/respond` accepts `response_type` of `ai_generated` or `template` only.
- Request schemas forbid extra fields (`model_config = ConfigDict(extra="forbid")`) and strip whitespace where it
  makes sense; response schemas use `from_attributes=True`.
- `guest_email` is `EmailStr` (needs `email-validator`); `content` is `Field(min_length=1, max_length=2000)`.
- JSON field names are the snake_case names in the assignment. Enums serialise as their string values.

## Responses

- `response_model=` and `status_code=` on every route decorator; `tags=[...]` per router; docstring = OpenAPI summary.
- `POST /messages/{id}/respond` and `/escalate` return the created `AutomatedResponse` (201). 
