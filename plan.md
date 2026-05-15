# Restaurant Finder – Project Plan

## 1. Project Overview
Restaurant Finder is a web application for discovering recommended restaurants and managing a personal list of restaurants the user has visited.

The project is built as a multi-stage system:
- Stage A: backend development with FastAPI
- Stage B: frontend development with React, including SQLite persistence

The goal is to build a clean and understandable full-stack project that keeps the system simple and easy to run locally.

---

## 2. Project Idea
The system combines two simple goals:

- discovering recommended restaurants
- managing a personal visited restaurants list

The application allows users to:
- explore recommended restaurants
- search restaurants by name
- filter restaurants by country
- filter restaurants by cuisine
- add restaurants to a personal visited list
- create visited restaurants manually
- update visited restaurant details
- delete restaurants from the visited list

This creates a simple but realistic product that combines discovery and personal management.

---

## 3. Main Entity
The main backend entity is **Restaurant**.

Each restaurant in the visited list includes the following fields:

- `id`
- `name`
- `city`
- `country`
- `cuisine`
- `price_level`
- `rating`
- `is_open`

These fields are enough to support useful restaurant management without unnecessary complexity.

---

## 4. Validation Rules
The backend validates incoming data before saving it.

Validation rules:
- `name` must not be empty
- `city` must not be empty
- `country` must not be empty
- `cuisine` must not be empty
- `price_level` must be between 1 and 5
- `rating` must be between 1.0 and 5.0
- `is_open` must be a boolean value

Normalization applied on input:
- trimming extra spaces from text fields
- title-casing city, country, and cuisine fields

Duplicate prevention:
- a restaurant with the same name, city, and country cannot be added twice
- duplicate check is case-insensitive

---

## 5. Design Approach
The project follows a simple layered structure:

- backend API layer (`app/main.py`)
- model/schema layer (`app/models.py`)
- database layer (`app/database.py`)
- repository layer (`app/repository.py`)
- dependency injection layer (`app/dependencies.py`)
- frontend UI layer (`frontend/src/`)

The backend handles API logic, the repository handles all SQLite queries, and the frontend communicates only with the backend API.

---

## 6. Development Stages

### Stage A – Backend
Stage A focuses on building the backend with FastAPI.

Completed:
- working FastAPI application
- restaurant CRUD operations
- input validation with Pydantic
- duplicate prevention (case-insensitive, by name + city + country)
- proper HTTP status codes
- automated tests with pytest
- Docker support

### Stage B – Frontend and Persistence
Stage B focuses on building a React frontend and adding persistent storage.

Completed:
- React frontend with Vite
- Discover page for restaurant recommendations
- search by restaurant name
- filter by country
- filter by cuisine
- My Visited page for managing the visited list
- create, update, and delete operations through the UI
- add a restaurant from Discover to My Visited
- duplicate prevention reflected in the UI
- SQLite persistence via Python's built-in `sqlite3` — data survives backend restarts
- each test runs against an isolated in-memory SQLite database
- Docker Compose for running frontend and backend together
- named Docker volume so container data survives restarts

---

## 7. API Endpoints

### Health
- `GET /health`

### Restaurants
- `GET /restaurants`
- `POST /restaurants`
- `GET /restaurants/{restaurant_id}`
- `PUT /restaurants/{restaurant_id}`
- `DELETE /restaurants/{restaurant_id}`

---

## 8. Frontend Features

### Discover Page
- browse recommended restaurants (hardcoded curated list)
- search by restaurant name
- filter by country
- filter by cuisine
- add a restaurant to the visited list
- restaurants already in the visited list are shown as disabled

### My Visited Page
- view all visited restaurants
- create a visited restaurant manually via form
- update an existing visited restaurant
- delete a visited restaurant
- open/closed status badge per restaurant

### Navigation
- navigation bar with Discover and My Visited links
- active link is visually highlighted

---

## 9. Testing
The backend includes automated tests for:
- health endpoint
- create restaurant (201 + correct payload)
- list restaurants
- get restaurant by id
- update restaurant
- delete restaurant
- duplicate prevention (409 on exact match and case-insensitive match)
- duplicate update prevention (409)
- missing restaurant (404 on get, update, delete)
- validation errors (422 for bad price_level, rating, missing fields)

Tests use an isolated in-memory SQLite database per test. The on-disk `restaurants.db` is never touched by the test suite.

---

## 10. Technology Stack

- Python 3.13
- FastAPI
- Pydantic
- SQLite (Python stdlib `sqlite3`)
- pytest
- React 19
- Vite
- JavaScript
- Docker
- Docker Compose
- uv

---

## 11. Project Structure

```text
RestaurantFinder/
|-- app/
|   |-- __init__.py
|   |-- main.py
|   |-- models.py
|   |-- database.py
|   |-- repository.py
|   `-- dependencies.py
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |   `-- Navbar.jsx
|   |   |-- data/
|   |   |   `-- restaurantsData.js
|   |   |-- pages/
|   |   |   |-- DiscoverPage.jsx
|   |   |   `-- VisitedPage.jsx
|   |   |-- api.js
|   |   |-- App.jsx
|   |   |-- App.css
|   |   `-- main.jsx
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|-- tests/
|   |-- __init__.py
|   |-- conftest.py
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
