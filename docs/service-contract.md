# Service Contract

All endpoints are served by the FastAPI backend at `http://localhost:8000`.

Interactive documentation is available at `http://localhost:8000/docs`.

## Authentication

Protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are obtained from `POST /token`. They expire after 30 minutes.

---

## Auth endpoints

### POST /auth/register

Register a new user account.

**Auth required:** No

**Request body:**
```json
{ "username": "alice", "password": "secret" }
```

**Responses:**

| Status | Body | Condition |
|--------|------|-----------|
| 201 | `{"id": 1, "username": "alice", "role": "user"}` | Created |
| 409 | `{"detail": "Username already taken"}` | Username exists |

---

### POST /token

Obtain a JWT access token. Uses OAuth2 password flow (form-encoded, not JSON).

**Auth required:** No

**Request body** (`application/x-www-form-urlencoded`):
```
username=alice&password=secret
```

**Responses:**

| Status | Body | Condition |
|--------|------|-----------|
| 200 | `{"access_token": "...", "token_type": "bearer"}` | Valid credentials |
| 401 | `{"detail": "Invalid credentials"}` | Wrong username or password |
| 429 | `{"detail": "Too many login attempts. Try again in a minute."}` | Rate limit exceeded (10 attempts / IP / 60 s); includes `Retry-After: 60` header |

---

### GET /auth/me

Return the currently authenticated user.

**Auth required:** Yes (any role)

**Responses:**

| Status | Body | Condition |
|--------|------|-----------|
| 200 | `{"id": 1, "username": "alice", "role": "user"}` | Valid token |
| 401 | `{"detail": "Not authenticated"}` | Missing or invalid token |

---

## Admin endpoints

### GET /admin/users

List all registered users.

**Auth required:** Yes — `role` must be `"admin"`

**Responses:**

| Status | Body | Condition |
|--------|------|-----------|
| 200 | `[{"id": 1, "username": "alice", "role": "user"}, ...]` | Success |
| 401 | `{"detail": "Not authenticated"}` | Missing or invalid token |
| 403 | `{"detail": "Admin access required"}` | Token valid but role is not admin |

---

## Restaurant endpoints

All restaurant endpoints require a valid Bearer token. Operations are scoped to the authenticated user — users cannot read or modify each other's restaurants.

### GET /restaurants

List the authenticated user's visited restaurants.

**Responses:**

| Status | Body |
|--------|------|
| 200 | `[{Restaurant}, ...]` — empty array if none |
| 401 | Missing or invalid token |

---

### POST /restaurants

Add a restaurant to the authenticated user's visited list.

**Request body:**
```json
{
  "name": "La Piazza",
  "city": "Tel Aviv",
  "country": "Israel",
  "cuisine": "Italian",
  "price_level": 3,
  "rating": 4.5,
  "is_open": true
}
```

Text fields are normalized server-side (trimmed and title-cased).

**Responses:**

| Status | Body | Condition |
|--------|------|-----------|
| 201 | `{Restaurant}` with server-generated `id` | Created |
| 409 | `{"detail": "..."}` | Duplicate name + city + country for this user |
| 422 | Validation error | Invalid field values |
| 401 | — | Missing or invalid token |

---

### GET /restaurants/{id}

Get a single restaurant by ID.

**Responses:**

| Status | Condition |
|--------|-----------|
| 200 | Found and owned by caller |
| 404 | Not found or owned by a different user |
| 401 | Missing or invalid token |

---

### PUT /restaurants/{id}

Replace a restaurant's fields.

**Request body:** same shape as `POST /restaurants`

**Responses:**

| Status | Condition |
|--------|-----------|
| 200 | Updated successfully |
| 404 | Not found or owned by a different user |
| 409 | Updated name + city + country conflicts with another of the user's restaurants |
| 422 | Validation error |
| 401 | Missing or invalid token |

---

### DELETE /restaurants/{id}

Delete a restaurant.

**Responses:**

| Status | Condition |
|--------|-----------|
| 204 | Deleted |
| 404 | Not found or owned by a different user |
| 401 | Missing or invalid token |

---

## Refresh job endpoints

### POST /refresh-jobs

Enqueue a background job that computes a personalized dining summary for the authenticated user.

**Auth required:** Yes

**Optional header:**

```
Idempotency-Key: <client-generated-uuid>
```

If present and the key was seen within the last 24 hours, the original `job_id` is returned immediately without enqueuing a second job. This makes the endpoint safe to retry on network failure.

**Response 202:**
```json
{ "job_id": "550e8400-e29b-41d4-a716-446655440000" }
```

**Responses:**

| Status | Condition |
|--------|-----------|
| 202 | Job enqueued (or idempotency hit returned existing job) |
| 401 | Missing or invalid token |

---

### GET /refresh-jobs/{job_id}

Poll the status of a refresh job.

**Auth required:** Yes — must be the same user who created the job.

**Response 200 — pending or running:**
```json
{ "status": "pending", "result": null, "finished_at": null, "error": null }
```

**Response 200 — done:**
```json
{
  "status": "done",
  "result": {
    "total_visited": 5,
    "top_cuisine": "Italian",
    "avg_rating": 4.2,
    "highest_rated": { "name": "Osteria Francescana", "rating": 4.9, "cuisine": "Italian" },
    "by_cuisine": {
      "Italian": { "count": 3, "avg_rating": 4.5 },
      "Japanese": { "count": 2, "avg_rating": 3.8 }
    }
  },
  "finished_at": "2026-01-01T12:00:00+00:00",
  "error": null
}
```

**Response 200 — failed:**
```json
{ "status": "failed", "result": null, "finished_at": null, "error": "..." }
```

**Responses:**

| Status | Condition |
|--------|-----------|
| 200 | Job found and owned by caller |
| 401 | Missing or invalid token |
| 403 | `{"detail": "Access denied"}` — job exists but belongs to a different user |
| 404 | `{"detail": "Job not found"}` — unknown job id |

---

## Utility endpoints

### GET /health

**Auth required:** No

**Response 200:**
```json
{ "status": "ok", "app": "Restaurant Finder" }
```
