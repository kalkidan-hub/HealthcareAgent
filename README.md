# ThePulse

ThePulse is a clinical support app for managing patient records, care notes, prescriptions, vitals, lab reports, summaries, reminders, and patient-facing chat.

It is designed for two roles:

- Doctors and clinical staff who enter and review care data.
- Patients who view their own history, get reminders, and chat with a history-aware assistant.

## Main Features

- Doctors can insert prescriptions, clinical notes, and vitals.
- Laboratory staff can add lab reports to a patient record.
- Doctors can view patient history and generated summaries of that history.
- Patients can view their history and receive recommendations based on their records and vitals.
- Patients can receive reminders about their current prescriptions.
- Patients can chat with an assistant that is aware of their health history.

## Typical Workflow

1. A doctor or lab staff member adds the latest clinical data.
2. The app stores the information under the patient record.
3. Doctors review the full history and summaries when making decisions.
4. Patients see a simplified view of their history, recommendations, and active prescriptions.
5. Patients can use the chat feature for more context-aware guidance.

## Setup

Set the required environment variables in `.env`, then start the app:

```bash
uvicorn main:app --reload
```

If you are using Docker, you can start the stack with:

```bash
docker compose up --build
```

Run tests with:

```bash
pytest
```

## Project Structure

- `main.py` starts the app.
- `backend/routers/` contains API routes.
- `backend/services/` contains business logic.
- `backend/models/` contains data models.
- `backend/infrastructure/` contains database and integration utilities.
- `tests/` contains the test suite.

## Notes

- The app uses patient and doctor roles.
- Protected endpoints expect bearer-token authentication.
- The backend is built to keep patient history, summaries, and reminders connected to the same record.