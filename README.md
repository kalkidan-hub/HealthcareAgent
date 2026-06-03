# ThePulse

ThePulse is a lightweight clinical assistant web app that helps clinicians and patients manage clinical notes, prescriptions, vitals, lab reports, and patient-facing recommendations and reminders.

**Main Capabilities**

- **Doctor inputs:** Insert prescriptions, clinical notes, and vitals.
- **Laboratory inputs:** Laboratory staff can add lab reports tied to patients.
- **Patient history & summaries:** Doctors can view full patient histories and automatically-generated summaries of encounters, vitals, labs, and prescriptions.
- **Patient-facing view:** Patients can view their own history, receive personalized recommendations based on their history and vitals, and get reminders for active prescriptions.
- **Health-aware chat:** Patients can chat with a health-history-aware assistant that uses their records for context-aware responses.

**Why this app**

This project is intended as a practical foundation for clinical workflows that need structured documentation (notes, prescriptions, vitals, lab reports) plus patient-facing features (summaries, reminders, conversational support).

**Quick Start**

1. Create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

2. Create an `.env` file in the project root (copy or adapt from existing examples if present) and set required environment variables (DB connection, secrets, API keys).

3. Run the app locally:

```bash
uvicorn main:app --reload
# or, with Docker
docker compose up --build
```

4. Run tests:

```bash
pytest
```

**Project Layout (key files)**

- Server entrypoint: [main.py](main.py)
- Requirements: [requirements.txt](requirements.txt)
- Docker compose: [docker-compose.yml](docker-compose.yml)
- Backend code: `backend/` (routers, services, models)
- Tests: [tests/test_app.py](tests/test_app.py)

**Feature Notes**

- Doctors: Use the doctor-facing routes to create and update `prescriptions`, clinical `notes`, and `vitals`. These are persistently stored and tied to patient records.
- Lab staff: Upload or record lab reports which become part of the patient's medical history and feed summary generation.
- Summaries: The app aggregates notes, vitals, labs, and prescriptions to generate clinician- and patient-facing summaries for quick review.
- Patient recommendations: The patient-facing logic analyzes recent vitals and history to provide tailored recommendations and reminders for ongoing prescriptions.
- Chat: The conversational interface is context-aware, using the patient's history to ground replies and guidance.

**Tech Stack**

- Python (FastAPI or similar web framework)
- Uvicorn for the ASGI server
- Docker for containerized runs
- Pytest for tests

**Development Tips**

- Inspect the router and service modules under `backend/routers/` and `backend/services/` to see available endpoints and business logic.
- Use `uvicorn main:app --reload` for iterative development.

**Contributing**

- Open an issue or PR describing the change.
- Keep changes small and focused; add tests for new behaviors.
