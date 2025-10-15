# Survey Response Orchestrator

Survey Response Orchestrator is a FastAPI-based service for authoring survey-style forms, collecting responses, and presenting a lightweight browser UI for running data collection sessions. The application persists form definitions, handles response validation, and exposes a version history to keep track of how a form evolves over time.

## Highlights

- **Dynamic form builder UI** – Navigate to `/ui/forms` to browse published forms, preview archived ones, and launch a responsive form-filling interface that renders questions and metadata-driven constraints dynamically in the browser.
- **Structured question metadata** – Enforce numeric ranges, custom placeholders, regex patterns, and labelled choice options directly from the form definition.
- **Versioning & archival controls** – Every published change to a form is captured in an immutable version log, while both forms and response groups can be archived (and later restored) to manage the lifecycle of data collection campaigns.
- **RESTful API** – Automate form management and response ingestion through a consistent JSON API suitable for integrations or custom clients.

## Getting Started

### Prerequisites

- Docker and Docker Compose (recommended for local development)
- Alternatively, Python 3.11+ with virtualenv support if you prefer running the app directly

### Run with Docker Compose

```bash
docker-compose up --build
```

The API will listen on `http://localhost:8000`. After the container starts you can:

- Open `http://localhost:8000/ui/forms` to launch the web UI.
- Explore interactive API documentation at `http://localhost:8000/docs`.

### Run directly with Uvicorn

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

By default the application stores data in `./data/orchestrator.db`. The folder is created automatically.

## API Overview

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `POST` | `/forms` | Create a form (version `1`) with questions and metadata. |
| `PUT` | `/forms/{slug}` | Publish a new version of an existing form. |
| `POST` | `/forms/{slug}/archive` | Archive or restore a form by sending `{ "archived": true|false }`. |
| `GET` | `/forms` | List forms. Use `?include_archived=true` to include archived entries. |
| `GET` | `/forms/{slug}` | Retrieve the latest version of a form. |
| `GET` | `/forms/{slug}/versions` | View the full version history including question snapshots. |
| `POST` | `/forms/{slug}/responses` | Submit a response to the current form version. |
| `GET` | `/forms/{slug}/responses` | List responses. Use `?include_archived=true` to include archived records. |
| `POST` | `/forms/{slug}/responses/{id}/archive` | Archive or restore a response by sending `{ "archived": true|false }`. |

### Form payload structure

```json
{
  "slug": "patient-intake",
  "title": "Patient Intake",
  "description": "Baseline assessment",
  "questions": [
    {
      "prompt": "How many hours do you sleep on average?",
      "type": "integer",
      "position": 1,
      "required": true,
      "metadata": { "min_value": 0, "max_value": 24 }
    },
    {
      "prompt": "Primary symptoms",
      "type": "long_text",
      "position": 2,
      "metadata": { "placeholder": "List symptoms separated by commas" }
    },
    {
      "prompt": "Preferred contact method",
      "type": "single_choice",
      "position": 3,
      "required": true,
      "metadata": {
        "options": [
          { "value": "email", "label": "Email" },
          { "value": "phone", "label": "Phone" },
          { "value": "sms", "label": "Text message" }
        ]
      }
    }
  ]
}
```

### Response payload structure

```json
{
  "respondent_identifier": "participant-123",
  "notes": "Baseline visit",
  "answers": [
    { "question_id": 1, "value": "7" },
    { "question_id": 2, "value": "Headache, fatigue" },
    { "question_id": 3, "value": "email" }
  ]
}
```

The service validates numeric inputs against configured `min_value`/`max_value`, enforces choice membership for single or multiple choice questions, and ensures all required questions are answered before a response is accepted.

## Versioning and Archival Strategy

- Each time a form is created or updated, the current question set is recorded in `form_versions`. The latest version remains editable, while historical versions are immutable.
- Archiving a form immediately prevents new responses from being created. You may restore a form at any time by posting `{ "archived": false }` to the same endpoint.
- Responses inherit the active form version at submission time, allowing historical analyses even if the form changes later. Responses can also be archived individually without deleting data.

## Front-end Experience

The bundled UI is implemented with vanilla JavaScript and uses the same public API:

- **Forms directory** – Lists active and archived forms, highlights current version numbers, and links to the response UI.
- **Dynamic renderer** – Generates inputs based on question types, including numeric constraints, regex patterns, placeholders, and labelled choice options.
- **Submission workflow** – Provides inline validation for required fields and surfaces API errors without reloading the page.
- **Version sidebar** – Displays a timestamped audit trail sourced from the form version log.

Because the UI consumes the public API, it can serve as a reference implementation for other clients.

## Project Structure

```
app/
├── crud.py          # Database access helpers (forms, versions, responses)
├── database.py      # SQLite engine & session factory
├── main.py          # FastAPI application and UI routes
├── models.py        # SQLAlchemy models with versioning & archival fields
├── schemas.py       # Pydantic request/response models & metadata validators
├── static/          # CSS and JavaScript assets for the UI
└── templates/       # Jinja2 templates for HTML views
```

## Development Tips

- When iterating on schema changes you may wish to delete `./data/orchestrator.db` to start fresh. The current project uses SQLAlchemy's `create_all` for schema management.
- Use the interactive docs at `/docs` to quickly exercise new endpoints.
- Run tests or linting before committing (none are bundled yet, but `uvicorn app.main:app --reload` provides hot reloading during development).

Contributions and feedback are welcome!
