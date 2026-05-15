# Restaurant Finder

## Description
Restaurant Finder is a full-stack web application for discovering recommended restaurants and managing a personal list of restaurants the user has visited.

The project is built with a FastAPI backend and a React frontend that communicates only with the backend API.

---

## EX2 Scope
This submission covers:
- **Stage A**: FastAPI backend with CRUD, validation, duplicate prevention, and automated tests
- **Stage B**: React frontend with Discover and My Visited pages
- **Persistence**: SQLite database — data survives backend restarts

Not included (out of scope for EX2):
- authentication or user accounts
- external database services such as PostgreSQL or MySQL
- Redis, background workers, or EX3-style service orchestration

The EX2 "small extra" is implemented through cuisine filtering and duplicate prevention in the visited list flow.

---

## Features

### Backend
- FastAPI REST API
- full CRUD for restaurants (`GET`, `POST`, `PUT`, `DELETE`)
- input validation with Pydantic (required fields, price_level 1–5, rating 1.0–5.0)
- text normalization (trim + title-case on name, city, country, cuisine)
- duplicate prevention — same name + city + country rejected with 409, case-insensitive
- SQLite persistence via Python's built-in `sqlite3` — no extra packages needed
- dependency injection pattern for the repository
- Swagger / OpenAPI docs at `/docs`
- automated tests with pytest (16 tests, all using isolated in-memory SQLite)

### Frontend
- React 19 + Vite
- Navbar with active-link highlighting
- **Discover page**: browse a curated list of top restaurants, search by name, filter by country, filter by cuisine, add to My Visited
- **My Visited page**: view, create, edit, and delete visited restaurants; shows cuisine, price level, rating, and open/closed status per entry
- duplicate restaurants shown as disabled in Discover once added
- error and success feedback messages in the UI

### Infrastructure
- Docker support for backend and frontend independently
- Docker Compose to run both together with a single command
- named Docker volume so data persists across container restarts

---

## Prerequisites
- Python 3.13
- [`uv`](https://docs.astral.sh/uv/) (Python package manager)
- Node.js and npm
- Docker Desktop (only needed for Docker Compose)

---

## Run the Backend Locally

From the project root:

```bash
uv run uvicorn app.main:app --reload
```

The backend starts at `http://127.0.0.1:8000`.

The SQLite database file (`restaurants.db`) is created automatically at the project root on the first request. It is excluded from Git via `.gitignore`.

---

## Backend API Documentation

FastAPI generates interactive docs automatically:

```
http://127.0.0.1:8000/docs
```

---

## Run Backend Tests

```bash
uv run pytest tests/ -v
```

All 16 tests pass. Each test uses a fresh isolated in-memory SQLite database — the on-disk `restaurants.db` is never touched by the test suite.

---

## Run the Frontend Locally

From the `frontend/` directory:

```bash
npm install
npm run dev
```

The frontend starts at `http://127.0.0.1:5173`.

The frontend expects the backend to be running at `http://127.0.0.1:8000`. This is the default and requires no configuration.

---

## Run Both Together with Docker Compose

From the project root:

```bash
docker compose up --build
```

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://127.0.0.1:5173      |
| Backend  | http://127.0.0.1:8000      |
| API docs | http://127.0.0.1:8000/docs |

In Docker, the database is stored at `/data/restaurants.db` inside the backend container, backed by the `restaurant_data` named volume. Data survives `docker compose down` (use `docker compose down --volumes` to also remove the data).

---

## API Endpoints

| Method   | Path                        | Description                  |
|----------|-----------------------------|------------------------------|
| `GET`    | `/health`                   | Health check                 |
| `GET`    | `/restaurants`              | List all restaurants         |
| `POST`   | `/restaurants`              | Create a restaurant          |
| `GET`    | `/restaurants/{id}`         | Get a restaurant by ID       |
| `PUT`    | `/restaurants/{id}`         | Update a restaurant          |
| `DELETE` | `/restaurants/{id}`         | Delete a restaurant          |

### Example request body

```json
{
  "name": "La Piazza",
  "city": "tel aviv",
  "country": "israel",
  "cuisine": "italian",
  "price_level": 3,
  "rating": 4.5,
  "is_open": true
}
```

Text fields are normalized server-side (trimmed and title-cased). Submitting `"city": "tel aviv"` stores and returns `"city": "Tel Aviv"`.

---

## Database

The backend uses **SQLite** via Python's built-in `sqlite3` module. No extra packages or setup is required.

| Context          | Database location                                    |
|------------------|------------------------------------------------------|
| Local dev        | `restaurants.db` in the project root (auto-created)  |
| Docker Compose   | `/data/restaurants.db` in the container (named volume) |
| Tests            | `:memory:` — fresh isolated DB per test, never on disk |

`restaurants.db` is listed in `.gitignore` and should not be committed.

---

## Project Structure

```text
RestaurantFinder/
|-- app/
|   |-- __init__.py
|   |-- main.py            # FastAPI app and routes
|   |-- models.py          # Pydantic models
|   |-- database.py        # SQLite connection and schema init
|   |-- repository.py      # CRUD queries
|   `-- dependencies.py    # FastAPI dependency injection
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |   `-- Navbar.jsx
|   |   |-- data/
|   |   |   `-- restaurantsData.js   # curated discover list
|   |   |-- pages/
|   |   |   |-- DiscoverPage.jsx
|   |   |   `-- VisitedPage.jsx
|   |   |-- api.js         # fetch wrappers for backend calls
|   |   |-- App.jsx
|   |   |-- App.css
|   |   `-- main.jsx
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|-- tests/
|   |-- __init__.py
|   |-- conftest.py        # per-test in-memory SQLite fixture
|   `-- test_restaurants.py
|-- .dockerignore
|-- .gitignore
|-- backend.Dockerfile
|-- frontend.Dockerfile
|-- docker-compose.yml
|-- pyproject.toml
|-- README.md
|-- plan.md
|-- restaurant_requests.http
`-- uv.lock
```

---

## REST Client Requests

`restaurant_requests.http` contains sample HTTP requests for all endpoints. Use it with the REST Client extension in VS Code.

---

## AI Assistance

This project was developed with assistance from **Claude** (Anthropic), an AI coding assistant, via the Claude Code CLI tool.

### What AI was used for

AI assistance was used for the following tasks across EX2:

- **SQLite migration**: designing and implementing `app/database.py`, rewriting `app/repository.py` from in-memory to SQLite queries, and updating `app/dependencies.py` with lazy connection initialization
- **Test infrastructure**: updating `tests/conftest.py` to use per-test in-memory SQLite databases with FastAPI `dependency_overrides`
- **UI/UX improvements**: refining `App.css` with a restaurant-themed color palette (warm amber, espresso tones), updating `DiscoverPage.jsx` and `VisitedPage.jsx` with labeled form fields and better layout, and adding Playfair Display typography
- **Documentation**: drafting sections of `README.md` and `plan.md`

### How outputs were verified

AI-generated code was reviewed and tested before being accepted into the project:

- `uv run pytest tests/ -v` was run after every backend change — all 16 tests pass
- The backend was verified via the Swagger UI at `/docs` and the `restaurant_requests.http` file
- The frontend was exercised manually through the Discover and My Visited pages, including search, filters, add, edit, delete, and duplicate prevention flows
- Docker Compose was verified with `docker compose up --build`

---

## Author
Adi Beker
