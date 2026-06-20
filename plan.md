# Restaurant Finder – Project Plan

## 1. Project Overview

Restaurant Finder is a full-stack web application for discovering restaurants across Israel, managing a personal visited list, and receiving AI-powered restaurant recommendations.

The project evolved across EX2 and EX3 into a multi-service system built around:

* a **React** frontend
* a **FastAPI** backend
* **Redis** for caching, rate limiting, and job state
* an **Arq** background worker for dining-summary jobs
* a dedicated **AI microservice** for constrained restaurant recommendations

The project currently runs as **five Docker Compose services**:

* frontend
* backend
* redis
* worker
* ai_service

---

## 2. Project Idea

The system combines four main goals:

* discovering restaurants across Israel through a shared catalogue
* managing a personal visited restaurants list per user
* generating a personalized dining summary in the background
* providing AI-powered restaurant recommendations from the Israeli discover catalogue

Users can:

* register and log in
* browse restaurants by city from the discover catalogue
* search and filter discover restaurants
* add restaurants to their visited list
* create, update, and delete visited restaurant entries
* trigger a background dining-summary job
* request an AI recommendation
* ask again for a different recommendation
* switch between light and dark mode
* access a profile page

---

## 3. Main Entities

### 3.1 User

Fields:

* `id`
* `username`
* `password_hash`
* `role` (`"user"` / `"admin"`)

### 3.2 Personal Restaurant

This is the user-scoped visited restaurant entity.

Fields:

* `id`
* `name`
* `city`
* `country`
* `cuisine`
* `price_level`
* `rating`
* `is_open`
* `user_id` (FK → `users.id`)

### 3.3 Discover Restaurant

This is the shared Israeli catalogue used by the Discover page and the AI recommendation flow.

Fields:

* `id`
* `osm_id`
* `name`
* `city`
* `country`
* `cuisine`
* `address`
* `lat`
* `lon`
* `price_level`
* `rating`
* `is_open`
* `last_updated`

### 3.4 Refresh Job State

Stored in Redis for async dining-summary processing.

Fields conceptually include:

* `job_id`
* `user_id`
* `status`
* `result`
* `error`

---

## 4. Validation Rules

### Personal restaurants

* `name`, `city`, `country`, `cuisine` must not be empty
* `price_level` must be 1–5
* `rating` must be 1.0–5.0
* `is_open` must be boolean
* text fields are trimmed and normalized
* duplicate prevention is scoped per user:

  * same `name + city + country` for the same user → `409`

### Users

* `username` must be unique
* passwords are stored hashed, never in plain text

### Discover catalogue

* discover restaurants are shared data, not user-owned
* seeded records are inserted only when the catalogue is empty
* OSM-ingested records are upserted by `osm_id`

---

## 5. Design Approach

The project uses a layered structure with clear responsibility boundaries.

| Layer                       | Files                        |
| --------------------------- | ---------------------------- |
| API routes                  | `app/main.py`                |
| Auth / JWT / permissions    | `app/auth.py`                |
| Pydantic models             | `app/models.py`              |
| Redis helpers               | `app/redis.py`               |
| SQLite schema               | `app/database.py`            |
| User restaurant queries     | `app/repository.py`          |
| Discover catalogue queries  | `app/discover_repo.py`       |
| Dependency injection        | `app/dependencies.py`        |
| Backend → AI service bridge | `app/ai_client.py`           |
| AI service                  | `ai_service/`                |
| Background worker           | `worker/main.py`             |
| Refresh CLI                 | `scripts/refresh.py`         |
| Discover ingest CLI         | `scripts/ingest_discover.py` |
| Frontend                    | `frontend/src/`              |

The project follows a **multi-service architecture**:

* backend owns auth, CRUD, discover API, and recommendation orchestration
* worker owns async dining-summary jobs
* ai_service owns constrained recommendation generation
* frontend owns the user-facing product experience

---

## 6. Development Stages

### EX2 — Stage A: Backend

* FastAPI REST API
* Restaurant CRUD with validation and duplicate prevention
* SQLite persistence (`sqlite3` stdlib)
* dependency injection pattern
* automated tests
* Docker support

### EX2 — Stage B: Frontend and Persistence

* React + Vite frontend
* Discover page with browse/search/filter/add flow
* My Visited page with create/edit/delete
* Docker Compose integration
* SQLite persistence via named volume

---

### EX3 — M1: Auth foundation

* `users` table
* bcrypt password hashing
* JWT with `iss` / `aud` / `sub` / `role` / `exp`
* `POST /auth/register`
* `POST /token`
* `GET /auth/me`
* `get_current_user`, `require_admin`

### EX3 — M2: Admin route

* `GET /admin/users`
* admin-only authorization

### EX3 — M3: Per-user restaurants

* `user_id` FK added to personal restaurants
* all CRUD operations scoped to `current_user.id`
* duplicate prevention scoped per user

### EX3 — M4: Redis infrastructure

* Redis client helpers
* rate limiting on login
* idempotency support for refresh jobs
* Compose integration with healthcheck

### EX3 — M5: Arq worker

* dedicated worker service
* async dining-summary computation
* Redis-backed job state lifecycle

### EX3 — M6: Refresh job API

* `POST /refresh-jobs`
* `GET /refresh-jobs/{job_id}`
* ownership checks
* idempotency-key support

### EX3 — M7: Refresh CLI

* async Typer CLI
* retry/backoff
* `Idempotency-Key`
* `X-Trace-Id`
* logfire spans

### EX3 — M8: Frontend auth UI

* Login / Register pages
* protected routes
* token persistence
* logout
* auth-aware navbar

### EX3 — M9: Frontend dining-summary UI

* dining-summary trigger button
* polling flow
* summary panel with:

  * total visited
  * top cuisine
  * average rating
  * highest rated
  * cuisine breakdown

### EX3 — M10: Documentation

* `README.md`
* `plan.md`
* `docs/EX3-notes.md`
* `docs/service-contract.md`
* `docs/security-checklist.md`
* `docs/runbooks/compose.md`

---

### Post-EX3 Product Refinements

### P1 — Discover catalogue upgrade

The old static Discover list was replaced with a backend-served Israeli catalogue.

#### P1-M0 — UI rename

* `"Refresh Recommendations"` renamed to `"Analyze My Dining Summary"`

#### P1-M1 — Discover schema + seed

* `discover_restaurants` table added
* `app/discover_seed.py` created
* auto-seeding on empty catalogue

#### P1-M2 — Discover backend API

* `GET /discover/cities`
* `GET /discover/restaurants`

#### P1-M3 — Discover ingest script

* `scripts/ingest_discover.py`
* optional ingestion from OpenStreetMap / Overpass
* city-by-city fetch and upsert

#### P1-M4 — Discover frontend integration

* Discover page now fetches from backend
* City dropdown replaces Country filter
* cuisine and search remain client-side

#### P1-M5 — Discover test/cleanup pass

* expanded discover tests
* removed obsolete static frontend data source

### P2 — AI recommendation service

A dedicated `ai_service` was introduced.

* separate FastAPI microservice
* backend integration via `app/ai_client.py`
* frontend AI recommendation panel
* Gemini integration
* fallback behavior
* later refinement: recommendations constrained to the Israeli discover catalogue only

### P3 — AI recommendation quality improvements

* visited restaurants excluded
* previously suggested restaurants excluded
* `Ask again` returns a different restaurant when alternatives exist
* backend builds candidate restaurant list from `discover_restaurants`
* ai_service acts as a constrained selector + explainer
* recommendations remain Israel-only

### P4 — UI / UX polish

* light and dark theme support
* refined Discover and Visited pages
* improved navbar
* improved auth screens
* Sign In page background image treatment
* refined warm restaurant-inspired visual identity

### P5 — Profile / account UX

* Profile page added
* user-facing account area integrated into navigation

---

## 7. API Endpoints

### Auth

* `POST /auth/register`
* `POST /token`
* `GET /auth/me`
* `POST /auth/change-password` 

### Admin

* `GET /admin/users`

### Utility

* `GET /health`

### Personal restaurants (auth required)

* `GET /restaurants`
* `POST /restaurants`
* `GET /restaurants/{id}`
* `PUT /restaurants/{id}`
* `DELETE /restaurants/{id}`

### Refresh jobs (auth required)

* `POST /refresh-jobs`
* `GET /refresh-jobs/{id}`

### Discover catalogue (auth required)

* `GET /discover/cities`
* `GET /discover/restaurants`

### AI recommendation (auth required)

* `GET /ai/recommendation`

---

## 8. Frontend Pages

### Discover Page (`/`)

* Browse Israeli discover restaurants from backend catalogue
* Filter by city
* Search by restaurant name
* Filter by cuisine
* Add restaurant to visited list
* Request AI recommendation
* Ask again for another recommendation
* Analyze dining summary
* Display async summary result


### My Visited Page (`/visited`)

* View all visited restaurants for the authenticated user
* Create restaurant manually
* Edit existing restaurant
* Delete restaurant

### Login Page (`/login`)

* Username + password form
* Styled restaurant-themed background
* Redirect to Discover on success

### Register Page (`/register`)

* Username + password form
* Redirect to Login on success

### Profile Page (`/profile`)

* Account information section
* user-facing profile area in the application shell
* View account details
* View username and role
* Change password via secure authenticated flow

---

## 9. Testing

The project test suite now covers:

* auth flows
* rate limiting
* refresh jobs
* refresh script
* restaurant CRUD
* user isolation
* worker logic
* discover seed behavior
* discover API
* discover ingest normalization/upsert
* AI recommendation flow
* ai_service Gemini/fallback logic

Current total:

* **122 automated tests**
* all passing

Tests use:

* in-memory SQLite
* fakeredis
* mocked AI behavior where appropriate
* no live Redis/DB required for normal automated coverage

---

## 10. Technology Stack

| Category          | Technology                        |
| ----------------- | --------------------------------- |
| Language          | Python 3.13                       |
| Backend framework | FastAPI + Uvicorn                 |
| Validation        | Pydantic v2                       |
| Auth              | PyJWT + passlib[bcrypt]           |
| Database          | SQLite (`sqlite3`)                |
| Cache / queue     | Redis 7                           |
| Worker            | Arq                               |
| HTTP client       | httpx                             |
| CLI               | Typer                             |
| Retries           | tenacity                          |
| Observability     | logfire                           |
| AI                | Gemini via dedicated `ai_service` |
| Testing           | pytest + anyio + fakeredis        |
| Frontend          | React + Vite                      |
| Containerization  | Docker + Docker Compose           |
| Package manager   | uv                                |

---

## 11. Project Structure

```text
RestaurantFinder/
├── ai_service/
│   ├── gemini_client.py
│   ├── main.py
│   └── models.py
├── app/
│   ├── ai_client.py
│   ├── auth.py
│   ├── database.py
│   ├── dependencies.py
│   ├── discover_repo.py
│   ├── discover_seed.py
│   ├── main.py
│   ├── models.py
│   ├── redis.py
│   └── repository.py
├── worker/
│   └── main.py
├── scripts/
│   ├── ingest_discover.py
│   └── refresh.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Navbar.jsx
│       │   └── ProtectedRoute.jsx
│       ├── pages/
│       │   ├── DiscoverPage.jsx
│       │   ├── VisitedPage.jsx
│       │   ├── LoginPage.jsx
│       │   ├── RegisterPage.jsx
│       │   └── ProfilePage.jsx
│       ├── api.js
│       ├── App.jsx
│       ├── App.css
│       └── main.jsx
├── tests/
│   ├── conftest.py
│   ├── test_ai_recommendation.py
│   ├── test_auth.py
│   ├── test_discover_api.py
│   ├── test_discover_seed.py
│   ├── test_gemini_client.py
│   ├── test_ingest_discover.py
│   ├── test_rate_limit.py
│   ├── test_refresh.py
│   ├── test_refresh_script.py
│   ├── test_restaurants.py
│   ├── test_user_isolation.py
│   └── test_worker.py
├── docs/
│   ├── EX3-notes.md
│   ├── service-contract.md
│   ├── security-checklist.md
│   └── runbooks/
│       └── compose.md
├── backend.Dockerfile
├── ai_service.Dockerfile
├── frontend.Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── plan.md
└── README.md
```

---

## 12. Notes

* Discover catalogue is Israel-focused
* AI recommendations are constrained to the discover catalogue
* `Ask again` excludes previously suggested restaurants
* Sign In background image is decorative only
* Docker Compose is the preferred end-to-end run mode

---

## 13. Author

Adi Beker
