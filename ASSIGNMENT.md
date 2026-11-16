# ASSIGNMENT.md — Base360.ai Practical Assessment

### Background

Base360.ai is building an AI operating system for short-term rental businesses. One core feature is **Guest Communication Automation** — a system that receives guest messages from multiple booking channels (Airbnb, Booking.com, direct), classifies them by intent, and routes them to the right handler (AI auto-reply, human agent, or maintenance team).

Your task is to build the **Guest Message Router API** — a backend service that ingests guest messages, classifies them, and manages automated responses.

### Requirements

#### 1. Data Models

**Property**
- `id` (UUID, PK)
- `name` (string, required)
- `channel` (enum: `airbnb`, `booking_dot_com`, `direct`, required)
- `external_listing_id` (string, required — the ID on the channel platform)
- `created_at` (datetime, auto)

**GuestMessage**
- `id` (UUID, PK)
- `property_id` (UUID, FK → Property, required)
- `guest_name` (string, required)
- `guest_email` (string, required, validated as email)
- `content` (text, required, min 1 char, max 2000 chars)
- `intent` (enum: `check_in`, `amenity_inquiry`, `maintenance_request`, `booking_question`, `other` — nullable on creation, set by classification)
- `status` (enum: `pending`, `classified`, `responded`, `escalated` — default `pending`)
- `created_at` (datetime, auto)

**AutomatedResponse**
- `id` (UUID, PK)
- `message_id` (UUID, FK → GuestMessage, required)
- `body` (text, required)
- `response_type` (enum: `ai_generated`, `template`, `escalation_notice`)
- `created_at` (datetime, auto)

#### 2. API Endpoints

**Properties**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/properties` | Create a property |
| `GET` | `/properties` | List properties (filter by `?channel=`, paginate with `?skip=` & `?limit=`) |
| `GET` | `/properties/{id}` | Get a single property |

**Guest Messages**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/messages` | Create a guest message (status defaults to `pending`) |
| `GET` | `/messages` | List messages (filter by `?property_id=`, `?status=`, `?intent=`, paginate) |
| `GET` | `/messages/{id}` | Get a single message with its property and responses |
| `PATCH` | `/messages/{id}/classify` | Classify a message — set `intent` and change `status` to `classified` |

**Automated Responses**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/messages/{id}/respond` | Create an automated response for a message. Body: `{"body": "...", "response_type": "ai_generated"}`. Sets message status to `responded`. |
| `POST` | `/messages/{id}/escalate` | Escalate a message. Creates an `AutomatedResponse` with `response_type = "escalation_notice"` and a default body. Sets message status to `escalated`. |

#### 3. Classification Logic

The `PATCH /messages/{id}/classify` endpoint should implement **simple keyword-based classification** (no external AI API needed):

| Keywords (case-insensitive) | Intent |
|------------------------------|--------|
| `check-in`, `checkin`, `arrival`, `keys`, `early`, `late` | `check_in` |
| `wifi`, `pool`, `gym`, `parking`, `amenities`, `towel` | `amenity_inquiry` |
| `broken`, `not working`, `leak`, `repair`, `maintenance`, `fix` | `maintenance_request` |
| `booking`, `reservation`, `cancel`, `refund`, `dates` | `booking_question` |
| (no match) | `other` |

If the message content contains multiple keyword categories, pick the **first matching category** in the order listed above.

#### 4. Validation & Error Handling

- All endpoints must return proper HTTP status codes (201 for creation, 400 for validation errors, 404 for not found, 422 for schema violations)
- `guest_email` must be a valid email format
- `content` must be 1–2000 characters
- `PATCH /messages/{id}/classify` on an already-classified message should return `409 Conflict`
- `POST /messages/{id}/respond` on a message with status `escalated` should return `409 Conflict`
- Non-existent `property_id` on message creation should return `404`

#### 5. Technical Constraints

- **Python + FastAPI**
- **SQLAlchemy** (async or sync — your choice)
- **SQLite** is fine for the database (no need for PostgreSQL)
- **Pydantic** for all request/response schemas
- Use `response_model=` on all endpoints
- Include a `requirements.txt`
- Include a `README.md` with setup and run instructions

#### 6. Bonus (Only If You Have Time)

- Add a `GET /properties/{id}/messages` endpoint that returns all messages for a property with their classification status summary (e.g., `{"total": 15, "pending": 5, "classified": 7, "responded": 2, "escalated": 1}`)
- Add unit tests for the classification logic
- Add rate limiting (e.g., max 10 message creations per minute per property)

---

### Rules

- **Time limit:** 2 hours from when you start
- **You may use:** AI assistants, documentation, any libraries, your own boilerplate
- **Commit frequently** — show your progress
- **The solution must run** — if the reviewer can't start it, it fails
- **Clean code matters** — meaningful names, error handling, proper structure

### Deliverable

A GitHub repository (or zip) containing:
1. Working FastAPI application
2. `requirements.txt`
3. `README.md` with run instructions
4. All endpoints functional and tested
