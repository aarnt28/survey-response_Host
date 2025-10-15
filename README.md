# Survey Response Orchestrator

This project provides a Python/FastAPI backend for orchestrating survey-style forms, storing form definitions, and capturing responses. It is designed to be the foundation for future extensions such as custom front-end experiences or integrations with other systems.

## Features

- Define reusable forms with ordered questions and metadata.
- Store responses for existing forms, supporting respondent identifiers and notes.
- Retrieve existing forms and their collected responses through a simple API.

## Getting Started

### Prerequisites

- Docker and Docker Compose installed locally.

### Running the API

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`. FastAPI's interactive docs are exposed at `http://localhost:8000/docs`.

### Project Layout

- `app/database.py` – database engine configuration and session utilities.
- `app/models.py` – SQLAlchemy models representing forms, questions, and responses.
- `app/schemas.py` – Pydantic schemas for request and response validation.
- `app/crud.py` – database helpers for working with forms and responses.
- `app/main.py` – FastAPI application entrypoint and API routes.

### Persistence

SQLite is used as the default persistence layer. Database files are stored under `./data` inside the container and mapped to a Docker volume (`orchestrator_data`) to persist data between runs.

### Next Steps

- Build a front-end for rendering and submitting forms dynamically.
- Add authentication and authorization for managing sensitive form data.
- Implement versioning or archival strategies for forms and responses.
- Expand question metadata to support richer validation (e.g., numeric ranges, choice labels).
