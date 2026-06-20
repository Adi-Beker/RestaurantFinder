# Docker Compose Runbook

## Required environment variables

All variables have defaults suitable for local development. Override them for any production-like deployment.

| Variable         | Default (in container)                  | Purpose                                                                     |
| ---------------- | --------------------------------------- | --------------------------------------------------------------------------- |
| `DB_PATH`        | `/data/restaurants.db`                  | SQLite file path inside the backend container                               |
| `REDIS_URL`      | `redis://redis:6379`                    | Redis connection string used by backend, worker, and Arq pool               |
| `JWT_SECRET`     | `dev-secret-do-not-use-in-production!!` | HMAC key for JWT signing — **must be overridden outside local development** |
| `AI_SERVICE_URL` | `http://ai_service:8001`                | Backend → AI service URL inside Docker Compose                              |
| `GEMINI_API_KEY` | *(unset)*                               | Gemini API key used by `ai_service`                                         |

To override values, use a `.env` file or define `environment` entries in `docker-compose.yml`.

---

## Start the stack

```bash
docker compose up --build
```

`--build` rebuilds images from source. Omit it on subsequent starts if the code has not changed.

To run in the background:

```bash
docker compose up --build -d
```

---

## Startup order

1. **redis** starts first and must pass its healthcheck (`redis-cli ping`).
2. **backend** starts after redis is healthy and must pass its healthcheck (`curl /health`).
3. **worker** starts after both redis and backend are healthy.
4. **ai_service** starts as part of the application stack and exposes its own `/health` endpoint.
5. **frontend** starts after the backend is healthy.

| Service    | Exposed port | URL                        |
| ---------- | ------------ | -------------------------- |
| frontend   | 5173         | http://localhost:5173      |
| backend    | 8000         | http://localhost:8000      |
| API docs   | —            | http://localhost:8000/docs |
| ai_service | 8001         | http://localhost:8001      |
| redis      | not exposed  | internal only              |

---

## Verify health

Backend health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","app":"Restaurant Finder"}
```

AI service health endpoint:

```bash
curl http://localhost:8001/health
```

Check all container statuses:

```bash
docker compose ps
```

All services should show `Up` and the healthchecked services should show `healthy`.

---

## Inspect logs

```bash
# all services
docker compose logs -f

# individual services
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f redis
docker compose logs -f ai_service
docker compose logs -f frontend
```

Useful things to look for:

* backend startup and `/health` checks
* worker job pickup / completion
* AI service recommendation requests
* Redis-backed idempotency / job state behavior

---

## Verify authentication and protected routes

Open the frontend:

```text
http://localhost:5173
```

Or use the API directly:

1. Register a user:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo-user","password":"demo-pass-123"}'
```

2. Log in and obtain a token:

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo-user&password=demo-pass-123"
```

3. Use the returned token against a protected route:

```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## Verify rate-limit behavior

The login endpoint is Redis-rate-limited. To verify that the stack exposes the expected rate-limit behavior, hit `/token` repeatedly with invalid credentials.

Example:

```bash
for i in {1..11}; do
  curl -i -X POST http://localhost:8000/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=demo-user&password=wrong-password"
done
```

Expected behavior:

* early attempts return `401 Unauthorized`
* after the configured limit is exceeded, the endpoint returns `429 Too Many Requests`

If your implementation includes rate-limit headers, inspect them in the `curl -i` response output.

You can also inspect Redis keys:

```bash
docker compose exec redis redis-cli KEYS 'rate:*'
```

---

## Verify refresh job flow

1. Log in and keep a valid JWT.
2. Trigger a refresh job:

```bash
curl -X POST http://localhost:8000/refresh-jobs \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Idempotency-Key: demo-refresh-1"
```

3. Poll the returned `job_id`:

```bash
curl http://localhost:8000/refresh-jobs/<JOB_ID> \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Expected behavior:

* initial state: `pending` or `running`
* final state: `done`
* response includes the dining summary result

If the same `Idempotency-Key` is reused, the server should return the original job instead of creating duplicate work.

To inspect stored refresh job hashes:

```bash
docker compose exec redis redis-cli KEYS 'job:*'
docker compose exec redis redis-cli HGETALL job:<JOB_ID>
```

---

## Verify AI recommendation flow

1. Ensure the discover catalogue is present and the user has at least one unvisited recommendation candidate.
2. Request a recommendation:

```bash
curl http://localhost:8000/ai/recommendation \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

3. Request another recommendation while excluding the previous one:

```bash
curl "http://localhost:8000/ai/recommendation?exclude=<PREVIOUS_NAME>" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Expected behavior:

* recommendations come only from the Israeli discover catalogue
* already visited restaurants are excluded
* excluded names are not repeated
* the AI service returns a recommendation only from the filtered candidate list

---

## Run pytest locally

From the repo root:

```bash
uv run pytest -v
```

Or a shorter version:

```bash
uv run pytest -q
```

This is the main local automated verification step for backend and service logic.

---

## Run Schemathesis / contract checks

If Schemathesis is installed in the project environment, run it against the live OpenAPI schema:

```bash
uv run schemathesis run http://localhost:8000/openapi.json --checks status_code_conformance
```

A lighter dry-run form can be used when needed:

```bash
uv run schemathesis run http://localhost:8000/openapi.json --checks status_code_conformance --dry-run
```

Use this after the stack is healthy and the backend is running.

---

## CI-aligned verification sequence

A grader or teammate can follow this local sequence before release:

1. Start the full stack:

```bash
docker compose up --build -d
```

2. Verify health:

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8001/health
```

3. Run automated tests:

```bash
uv run pytest -v
```

4. Run contract checks:

```bash
uv run schemathesis run http://localhost:8000/openapi.json --checks status_code_conformance --dry-run
```

5. Build the frontend when needed:

```bash
cd frontend && npm run build
```

---

## Stop the stack

Stop without removing data:

```bash
docker compose down
```

Stop and remove all named volumes:

```bash
docker compose down --volumes
```

This deletes the SQLite database and Redis data.

---

## Reset Redis

Clear all keys without restarting containers:

```bash
docker compose exec redis redis-cli FLUSHALL
```

Or remove the Redis volume and restart:

```bash
docker compose down
docker volume rm restaurantfinder_redis_data
docker compose up -d
```

This clears:

* rate-limit counters
* idempotency keys
* refresh job hashes
* other Redis-backed transient state

---

## Reset SQLite data

Delete the database file inside the backend container:

```bash
docker compose exec backend rm /data/restaurants.db
docker compose restart backend worker
```

`init_schema` recreates the schema automatically on next startup.

Or remove the data volume entirely:

```bash
docker compose down --volumes
docker compose up --build
```

This removes:

* users
* visited restaurants
* discover catalogue contents
* application-local SQLite data

---

## Troubleshooting

### Docker stack does not start

* confirm Docker Desktop is running
* rerun `docker compose up --build`
* inspect `docker compose logs -f`

### Redis connection refused

* confirm redis is healthy in `docker compose ps`
* inspect `docker compose logs redis`

### Backend unhealthy

* inspect:

```bash
docker compose logs backend
```

* verify `JWT_SECRET`, `REDIS_URL`, and `DB_PATH`

### AI recommendations fail

* verify:

```bash
docker compose logs ai_service
```

* confirm `GEMINI_API_KEY` is set when using live Gemini integration
* if Gemini is unavailable, verify fallback behavior still works

### Schemathesis fails immediately

* confirm backend is running and reachable at `http://localhost:8000`
* open `http://localhost:8000/openapi.json` in a browser or with `curl`

### Rate-limit test behaves unexpectedly

* reset Redis:

```bash
docker compose exec redis redis-cli FLUSHALL
```

* then rerun the login loop
