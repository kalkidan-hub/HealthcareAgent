# HealthcareAgent

FastAPI backend with PostgreSQL persistence for prescriptions, lab reports, clinical notes, and patient metadata.
This project requires a running PostgreSQL instance as the primary datastore; the app will fail to start if it cannot connect to the configured `DATABASE_URL`.

## Database

Set `DATABASE_URL` before running the app:

```bash
set DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/healthcareagent
```

To run PostgreSQL locally with Docker:

```bash
docker compose up -d postgres
```

Create the database in PostgreSQL first, then start the app:

```bash
uvicorn main:app --reload
```

On startup, the app tries to create the required tables automatically. If PostgreSQL is down, the app switches to the SQLite fallback automatically.

## API

The main endpoints are mounted under `/api`:

- `POST /api/add-prescription`
- `GET /api/get-prescription?patient_id=...`
- `POST /api/add-clinical-note`
- `GET /api/get-clinical-note?patient_id=...`
- `POST /api/add-lab-report`
- `GET /api/get-lab-report?patient_id=...&report_date=...`
- `POST /api/talk`