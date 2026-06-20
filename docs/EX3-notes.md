# EX3 Design Notes

## Key design decisions

### PyJWT over python-jose

PyJWT was chosen because it handles HS256 signing and verification with a minimal footprint. `python-jose` supports JWK sets and RS256, which are not needed here. PyJWT also has no transitive dependency on `cryptography` for HMAC-only usage, keeping the install smaller and simpler for a local course project.

### Arq over alternatives for the background worker

Three alternatives were considered:

| Option           | Reason rejected                                                                             |
| ---------------- | ------------------------------------------------------------------------------------------- |
| Celery + broker  | Heavyweight; requires more setup and usually a separate result backend in addition to Redis |
| RQ               | Sync-first; awkward with an async FastAPI codebase                                          |
| Raw asyncio task | No proper job tracking, no worker process separation, no queue lifecycle                    |

Arq was chosen because it is async-native, uses Redis for both the queue and job metadata, and has a small API surface. The `WorkerSettings` pattern maps cleanly onto the project’s FastAPI + Redis architecture.

### Per-request Arq pool

`get_arq_pool()` creates and closes a pool per request rather than using a module-level singleton. For a course project with low concurrency this is acceptable and avoids lifecycle complexity. A production service would typically manage the pool at application startup and shutdown.

### Async `POST /refresh-jobs`, sync `GET /refresh-jobs/{job_id}`

`POST /refresh-jobs` is implemented as `async def` because it awaits `arq.enqueue_job`. `GET /refresh-jobs/{job_id}` is implemented as `def` because the Redis access pattern used there is synchronous; FastAPI automatically runs sync routes inside a thread pool.

### Idempotency-Key on `POST /refresh-jobs`

Clients that retry on network failure risk enqueuing duplicate jobs. The `Idempotency-Key` header (stored in Redis with a 24-hour TTL) ensures that repeating the same logical request returns the original `job_id` without creating duplicate work.

The header is optional; omitting it keeps normal non-idempotent behavior.

### User-scoped refresh jobs

The Redis job hash stores `user_id` alongside `status`. `GET /refresh-jobs/{job_id}` returns `403` if the authenticated user does not own the job. This prevents users from polling one another’s refresh jobs.

### logfire in `scripts/refresh.py`

`logfire.configure(send_to_logfire=False)` is called before spans are opened. This sends telemetry to local stdout/stderr only, which keeps the project local-first and avoids requiring an external account during development and grading.

A production-style setup could switch to a real Logfire project by setting a token and removing the `send_to_logfire=False` development setting.

### tenacity retry in `scripts/refresh.py`

The refresher uses bounded retry with exponential backoff:

* 3 total attempts
* 1s / 2s / 4s style retry spacing (bounded)
* same `Idempotency-Key` reused across retries
* fresh trace context per logical run where appropriate

This means the client can retry safely without duplicating the underlying job on the server.

### Shared Israeli discover catalogue

The original EX2-style static frontend list was replaced with a backend-served Israeli discover catalogue. This was done to make the product feel more realistic, easier to extend, and better aligned with the AI recommendation flow.

The catalogue is stored in `discover_restaurants` and can be populated in two ways:

* curated seed data for reliable local cold start
* optional OSM / Overpass ingestion via `scripts/ingest_discover.py`

### Dedicated AI microservice

A separate `ai_service` was introduced to keep recommendation-generation concerns outside the main API. This matches the EX3 microservice direction more clearly than embedding all recommendation logic directly in the backend.

The backend remains the orchestration layer:

* it authenticates the user
* reads visited restaurants
* builds the candidate list from the Israeli discover catalogue
* excludes already visited and previously suggested restaurants
* sends a constrained request to `ai_service`

The `ai_service` acts as a **selector + explainer**, not a free-form generator.

### Constrained recommendation strategy

The recommendation flow was intentionally redesigned so that AI recommendations come **only** from the project’s Israeli discover catalogue.

This prevents several problems:

* recommending restaurants outside Israel
* recommending restaurants that do not exist in the app’s catalogue
* repeating the same 1–2 famous places over and over
* recommending restaurants the user already visited

The final behavior is:

* backend builds a filtered candidate list
* candidate list excludes visited restaurants
* candidate list excludes previously suggested restaurants when the user asks again
* AI must choose only from that list
* fallback logic also respects the same filtered list

This makes the recommendation feature deterministic enough for grading while still benefiting from AI-generated explanation text.

---

## Security notes

### Password hashing

Passwords are never stored in plaintext. They are hashed with bcrypt through passlib before persistence.

### JWT claims

Access tokens include:

* `iss`
* `aud`
* `sub`
* `role`
* `exp`

At least one protected route uses role-based checks, and tests cover authorization failures.

### Secret hygiene

Local development uses a default `JWT_SECRET`, but this is not appropriate outside local development.

The project keeps:

* `.env` out of version control
* `.env.example` / documented variables aligned with local setup
* no committed SQLite `.db` artifacts

### JWT secret rotation steps

If secret rotation is required:

1. Stop the running stack
2. Change `JWT_SECRET` in the local environment or `.env`
3. Restart backend and related services
4. Re-authenticate users so new tokens are minted with the new secret
5. Discard old tokens, since they will no longer validate under the rotated secret

For a local course project, manual rotation is sufficient and documented here for reproducibility.

---

## Telemetry / trace excerpt

The refresh flow carries both tracing and idempotency information.

Example excerpt from the async refresh path:

```text id="7g2n7t"
POST /refresh-jobs
X-Trace-Id: refresh-run-001
Idempotency-Key: refresh-user-1-job-001

→ response: 202 Accepted
→ returned job_id: 9f1b1d2e-...
→ repeated POST with same Idempotency-Key returns the same job_id
```

This demonstrates the intended EX3 reliability path:

* requests are traceable
* retries are safe
* duplicate work is prevented by Redis-backed idempotency

---

## Migration note — deleting EX2 `restaurants.db`

EX3 adds a `user_id INTEGER NOT NULL REFERENCES users(id)` column to the personal `restaurants` table.

Any `restaurants.db` created by EX2 (before this column existed) can cause schema mismatch problems because `CREATE TABLE IF NOT EXISTS` will not rebuild the old table automatically.

**Before running EX3 for the first time, delete the old database:**

```bash id="4r8njy"
# local dev
rm restaurants.db

# Docker Compose (removes all named volumes)
docker compose down --volumes
```

A fresh database is created automatically on the next startup.

---

## Final EX3 release notes

By the end of EX3, the project includes:

* JWT authentication and role-protected routes
* per-user restaurant CRUD
* Redis-backed idempotent refresh jobs
* Arq background worker
* async refresh CLI
* dedicated AI recommendation service
* Israeli discover catalogue with seed/ingest support
* constrained AI recommendations
* profile page with password-change flow
* polished light/dark UI and documented local runbook
