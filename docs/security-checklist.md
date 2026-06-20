# Security Checklist

## Implemented

### Password hashing
Passwords are hashed with bcrypt via `passlib[bcrypt]` before storage. Plain-text passwords are never persisted or logged. `bcrypt<4.0.0` is pinned because passlib 1.7.4 is incompatible with bcrypt 5.x (the newer version enforces a 72-byte limit during passlib's internal probe).

### JWT claims
Every token includes the following claims:

| Claim | Value |
|-------|-------|
| `iss` | `"restaurant-finder"` |
| `aud` | `"restaurant-finder-api"` |
| `sub` | username |
| `role` | `"user"` or `"admin"` |
| `exp` | issued-at + 30 minutes |

Tokens are signed with HS256. The signature is verified on every protected request; a tampered or expired token returns 401.

### Token expiry
Access tokens expire after 30 minutes. There is no refresh token — users must re-authenticate after expiry.

### Admin-only route
`GET /admin/users` is guarded by the `require_admin` dependency. Any valid token with `role != "admin"` receives 403. Registering via `POST /auth/register` always creates a `role = "user"` account; admin accounts must be set directly in the database.

### Rate limiting on login
`POST /token` limits each IP address to 10 attempts per 60-second window using a Redis `INCR` / `EXPIRE` counter. Exceeding the limit returns 429 with a `Retry-After: 60` header.

### Per-user data isolation
All restaurant CRUD queries include `AND user_id = ?`. A user cannot read, update, or delete another user's restaurants — mismatched IDs return 404 (indistinguishable from not found).

### Refresh job ownership
`POST /refresh-jobs` stores `user_id` in the Redis job hash. `GET /refresh-jobs/{job_id}` returns 403 if the authenticated user's ID does not match the stored value. Job IDs are UUIDs (v4, random) and are not guessable.

### SQL injection prevention
All database queries use parameterized statements (`?` placeholders). No string interpolation is used in SQL.

---

## Intentionally not implemented

| Concern | Reason |
|---------|--------|
| HTTPS / TLS | Handled by a reverse proxy (nginx, Caddy) in any real deployment; terminating TLS in the application container is out of scope for a course project |
| Refresh token rotation | Access tokens are short-lived (30 min); adding a refresh token flow would increase complexity beyond the assignment scope |
| CSRF protection | The frontend communicates via `fetch` with `Authorization: Bearer` headers, not form submissions with cookies — CSRF does not apply to this flow |
| Token revocation / blocklist | Stateless JWTs cannot be revoked before expiry without a server-side blocklist; not required for this project |
| Password strength enforcement | No minimum length or complexity rules — kept simple for the course context |
| HTTPS-only cookies | Token is stored in `localStorage`, not a cookie — simpler but means XSS on the frontend could expose the token |
