# ThePulse

FastAPI backend with PostgreSQL persistence for prescriptions, lab reports, clinical notes, and user metadata.
Users authenticate with bearer tokens, and user-facing IDs are UUIDs instead of integers.

## Database

Copy `.env.example` to `.env` and set your local database settings. At minimum, set `POSTGRES_PASSWORD` for Docker and `DATABASE_URL` for the app:

```bash
POSTGRES_PASSWORD=your_password
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/healthcareagent
```

Set `DATABASE_URL` before running the app if you are not using a `.env` file:

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

On startup, the app tries to create the required tables automatically.

## Authentication

The API exposes two user roles: `patient` and `doctor`.

- `POST /api/auth/register` creates a user and returns a bearer token.
- `POST /api/auth/login` returns a bearer token for an existing user.
- `GET /api/auth/me` returns the authenticated user profile.
- `PUT /api/auth/me` updates the authenticated user profile.

Registration accepts optional profile fields for `sex`, `contact_number`, and `emergency_number`.

Send the token in the `Authorization: Bearer <token>` header for protected routes.

## API

The main endpoints are mounted under `/api`:

- `GET /api/patients` doctor-only patient list with profile, chief complaint, alerts, and last update
- `POST /api/add-prescription`
- `GET /api/get-prescription?patient_id=<uuid>`
- `POST /api/add-clinical-note`
- `GET /api/get-clinical-note?patient_id=<uuid>`
- `POST /api/add-lab-report`
- `GET /api/get-lab-report?patient_id=<uuid>&report_date=...`
- `POST /api/add-vitals`
- `GET /api/get-vitals?patient_id=<uuid>&recorded_at=...`
- `GET /api/get-vitals-history?patient_id=<uuid>`
- `PUT /api/update-vitals/{patient_id}/{recorded_at}`
- `DELETE /api/delete-vitals/{patient_id}/{recorded_at}`
- `POST /api/summarize` with `{ "patient_id": "<uuid>" }`
- `GET /api/recommend` for the logged-in patient
- `GET /api/remind` for the logged-in patient
- `POST /api/talk` with patient-side conversation memory
