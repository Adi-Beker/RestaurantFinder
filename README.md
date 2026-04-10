# Restaurant Finder

## Description
Restaurant Finder is a FastAPI-based backend project for managing restaurant data.

This version represents the backend foundation of the system and supports full CRUD operations for restaurants.

## Stage
This repository currently contains **Stage A** of the project.

Stage A includes:
- FastAPI backend
- full restaurant CRUD operations
- input validation with Pydantic
- dependency injection
- automated tests with pytest
- Docker support

The repository includes automated tests for Stage A.

## Prerequisites
Before running the project, make sure the following tools are installed:

- Python 3.13 
- `uv`
- Docker Desktop, if you want to run the project in a container

## Features
- FastAPI backend
- CRUD operations for restaurants
- Input validation with Pydantic
- In-memory repository
- Dependency injection
- Automated tests with pytest
- Swagger/OpenAPI documentation
- Docker support

## Technologies
- Python
- FastAPI
- Pydantic
- pytest
- uv
- Docker

## Run the Project
Run the backend locally with:

```bash
uv run uvicorn app.main:app --reload
```

The application will run locally at:

```text
http://127.0.0.1:8000
```

## API Documentation
FastAPI automatically provides interactive Swagger/OpenAPI documentation.

After running the server, open:

```text
http://127.0.0.1:8000/docs
```

## Run Tests
Run all tests with:

```bash
uv run pytest tests -v
```

## Run with Docker

### Build the image
```bash
docker build -t restaurant-finder .
```

### Run the container
```bash
docker run --rm -p 8000:8000 --name restaurant-finder restaurant-finder
```

After the container starts, open:

```text
http://127.0.0.1:8000/docs
```

## Available Endpoints

### Health Check
- `GET /health`

### Restaurants
- `GET /restaurants`
- `POST /restaurants`
- `GET /restaurants/{restaurant_id}`
- `PUT /restaurants/{restaurant_id}`
- `DELETE /restaurants/{restaurant_id}`

## Example Request Body
Example JSON for creating a restaurant:

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

## Project Structure
```text
EASS-PROJECT-Resturant-Finder/
|-- app/
|   |-- __init__.py
|   |-- main.py
|   |-- models.py
|   |-- repository.py
|   `-- dependencies.py
|-- tests/
|   |-- __init__.py
|   |-- conftest.py
|   `-- test_restaurants.py
|-- .gitignore
|-- Dockerfile
|-- plan.md
|-- pyproject.toml
|-- uv.lock
`-- README.md
```
## REST Client Requests
The file `restaurant_requests.http` contains sample HTTP requests for manually testing the API endpoints.
It can be used with the REST Client extension in VS Code.

## Current Status
This stage includes the backend only.

The project currently supports:
- restaurant CRUD operations
- request validation
- automated testing
- Docker execution

At this stage:
- data is stored in memory
- there is no frontend yet
- there is no persistent database yet

## Notes
The current repository folder name uses the spelling `Resturant`.
The product name used in the project documentation is `Restaurant Finder`.
This naming inconsistency can be cleaned up later.

## Author
Adi Beker