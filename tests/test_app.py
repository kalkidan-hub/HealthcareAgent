import os
from datetime import date, datetime, timezone
from uuid import UUID

os.environ.setdefault("DATABASE_URL", "sqlite:///./.test-healthcareagent.db")

import pytest
from fastapi.testclient import TestClient

import main
from backend.infrastructure.auth import get_current_user as get_current_user_dependency
from backend.models.auth import CurrentUser, UserRole
from backend.routers import auth as auth_router
from backend.routers import clinical_notes as clinical_notes_router
from backend.routers import lab_report as lab_report_router
from backend.routers import patients as patients_router
from backend.routers import prescription as prescription_router
from backend.routers import summary as summary_router
from backend.routers import talk as talk_router
from backend.routers import vitals as vitals_router


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "init_db", lambda: None)
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    main.app.dependency_overrides.clear()
    yield
    main.app.dependency_overrides.clear()


def _user(user_id: str, role: UserRole) -> CurrentUser:
    return CurrentUser(
        id=UUID(user_id),
        name="Dr. Who" if role == UserRole.doctor else "Ada Lovelace",
        email="doctor@example.com" if role == UserRole.doctor else "patient@example.com",
        role=role,
        age=42,
    )


def _set_current_user(user: CurrentUser) -> None:
    main.app.dependency_overrides[get_current_user_dependency] = lambda: user


class FakeResponse:
    def __init__(self, text: str):
        self.text = text


def test_register_returns_token_and_user(client, monkeypatch):
    user_id = "11111111-1111-1111-1111-111111111111"

    def fake_create_user_account(**kwargs):
        assert kwargs["name"] == "Ada Lovelace"
        assert kwargs["email"] == "ada@example.com"
        assert kwargs["password"] == "supersecret"
        assert kwargs["role"].value == "patient"
        return {
            "id": user_id,
            "name": kwargs["name"],
            "email": kwargs["email"],
            "role": kwargs["role"],
            "age": kwargs["age"],
            "sex": kwargs["sex"],
            "contact_number": kwargs["contact_number"],
            "emergency_number": kwargs["emergency_number"],
        }

    monkeypatch.setattr(auth_router, "create_user_account", fake_create_user_account)
    monkeypatch.setattr(auth_router, "create_access_token", lambda account_id: "test-token")

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "supersecret",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "access_token": "test-token",
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "role": "patient",
            "age": None,
            "sex": None,
            "contact_number": None,
            "emergency_number": None,
        },
    }


def test_login_returns_token_and_user(client, monkeypatch):
    user_id = "22222222-2222-2222-2222-222222222222"

    monkeypatch.setattr(
        auth_router,
        "authenticate_user",
        lambda email, password: {
            "id": user_id,
            "name": "Ada Lovelace",
            "email": email,
            "role": UserRole.patient,
            "age": 34,
            "sex": None,
            "contact_number": None,
            "emergency_number": None,
        },
    )
    monkeypatch.setattr(auth_router, "create_access_token", lambda account_id: "login-token")

    response = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "supersecret"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "login-token"
    assert response.json()["user"]["email"] == "ada@example.com"


def test_me_returns_current_user(client):
    user = _user("33333333-3333-3333-3333-333333333333", UserRole.patient)
    _set_current_user(user)

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    assert response.json()["role"] == "patient"


def test_update_me_updates_profile(client, monkeypatch):
    user = _user("44444444-4444-4444-4444-444444444444", UserRole.patient)
    _set_current_user(user)

    monkeypatch.setattr(
        auth_router,
        "upsert_patient_profile",
        lambda patient_id, **kwargs: {
            "id": patient_id,
            "name": kwargs["name"],
            "email": kwargs["email"],
            "role": UserRole.patient,
            "age": kwargs["age"],
            "sex": kwargs["sex"],
            "contact_number": kwargs["contact_number"],
            "emergency_number": kwargs["emergency_number"],
        },
    )

    response = client.put(
        "/api/auth/me",
        json={
            "name": "Ada Byron",
            "email": "ada.byron@example.com",
            "age": 35,
            "sex": "female",
            "contact_number": "123",
            "emergency_number": "456",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Ada Byron"
    assert response.json()["contact_number"] == "123"


def test_patient_history_returns_items(client, monkeypatch):
    user = _user("55555555-5555-5555-5555-555555555555", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(
        auth_router,
        "get_patient_history",
        lambda patient_id: [
            {
                "event_type": "visit",
                "occurred_at": datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
                "payload": {"note": "checkup"},
            }
        ],
    )

    response = client.get("/api/patient_history")

    assert response.status_code == 200
    assert response.json()["items"][0]["event_type"] == "visit"


def test_doctor_patient_history_endpoint_allows_doctor(client, monkeypatch):
    user = _user("66666666-6666-6666-6666-666666666666", UserRole.doctor)
    _set_current_user(user)
    patient_id = "77777777-7777-7777-7777-777777777777"
    monkeypatch.setattr(auth_router, "get_patient_history", lambda patient_id: [])

    response = client.get(f"/api/patient_history/{patient_id}")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_add_clinical_note(client, monkeypatch):
    user = _user("88888888-8888-8888-8888-888888888888", UserRole.doctor)
    _set_current_user(user)
    monkeypatch.setattr(clinical_notes_router, "upsert_clinical_note", lambda note: note.model_dump())

    response = client.post(
        "/api/add-clinical-note",
        json={"patient_id": str(user.id), "note": "Follow-up in two weeks."},
    )

    assert response.status_code == 200
    assert response.json()["note"] == "Follow-up in two weeks."


def test_update_clinical_note(client, monkeypatch):
    user = _user("99999999-9999-9999-9999-999999999999", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(clinical_notes_router, "db_update_clinical_note", lambda note: note.model_dump())

    response = client.put(
        f"/api/update-clinical-note/{user.id}",
        json={"patient_id": str(user.id), "note": "Updated note."},
    )

    assert response.status_code == 200
    assert response.json()["note"] == "Updated note."


def test_delete_clinical_note(client, monkeypatch):
    user = _user("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(clinical_notes_router, "db_delete_clinical_note", lambda patient_id: True)

    response = client.delete(f"/api/delete-clinical-note/{user.id}")

    assert response.status_code == 204


def test_get_clinical_note(client, monkeypatch):
    user = _user("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(
        clinical_notes_router,
        "db_get_clinical_note",
        lambda patient_id: {"patient_id": str(patient_id), "note": "Existing note."},
    )

    response = client.get(f"/api/get-clinical-note?patient_id={user.id}")

    assert response.status_code == 200
    assert response.json()["note"] == "Existing note."


def test_add_lab_report(client, monkeypatch):
    user = _user("cccccccc-cccc-cccc-cccc-cccccccccccc", UserRole.doctor)
    _set_current_user(user)
    monkeypatch.setattr(lab_report_router, "upsert_lab_report", lambda report: report.model_dump())

    response = client.post(
        "/api/add-lab-report",
        json={
            "patient_id": str(user.id),
            "name": "Hemoglobin",
            "type": "Blood",
            "report_date": "2026-01-01T00:00:00+00:00",
            "result_value": 13.5,
            "unit": "g/dL",
            "normal_range": "12-16",
            "status": "normal",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Hemoglobin"


def test_update_lab_report(client, monkeypatch):
    user = _user("dddddddd-dddd-dddd-dddd-dddddddddddd", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(lab_report_router, "db_update_lab_report", lambda report: report.model_dump())

    response = client.put(
        f"/api/update-lab-report/{user.id}/2026-01-01",
        json={
            "patient_id": str(user.id),
            "name": "Hemoglobin",
            "type": "Blood",
            "report_date": "2026-01-01T00:00:00+00:00",
            "result_value": 13.7,
            "unit": "g/dL",
            "normal_range": "12-16",
            "status": "normal",
        },
    )

    assert response.status_code == 200
    assert response.json()["result_value"] == 13.7


def test_delete_lab_report(client, monkeypatch):
    user = _user("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(lab_report_router, "db_delete_lab_report", lambda patient_id, report_date: True)

    response = client.delete(f"/api/delete-lab-report/{user.id}/2026-01-01")

    assert response.status_code == 204


def test_get_lab_report(client, monkeypatch):
    user = _user("ffffffff-ffff-ffff-ffff-ffffffffffff", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(
        lab_report_router,
        "db_get_lab_report",
        lambda patient_id, report_date: {
            "patient_id": str(patient_id),
            "name": "Hemoglobin",
            "type": "Blood",
            "report_date": "2026-01-01T00:00:00+00:00",
            "result_value": 13.5,
            "unit": "g/dL",
            "normal_range": "12-16",
            "status": "normal",
        },
    )

    response = client.get(f"/api/get-lab-report?patient_id={user.id}&report_date=2026-01-01")

    assert response.status_code == 200
    assert response.json()["name"] == "Hemoglobin"


def test_add_prescription(client, monkeypatch):
    user = _user("12121212-1212-1212-1212-121212121212", UserRole.doctor)
    _set_current_user(user)
    monkeypatch.setattr(prescription_router, "upsert_prescription", lambda prescription: prescription.model_dump())

    response = client.post(
        "/api/add-prescription",
        json={
            "patient_id": str(user.id),
            "type": "Medication",
            "description": "Take one tablet daily.",
            "frequency": "daily",
            "start_date": "2026-01-01",
            "end_date": "2026-02-01",
            "calendar_path": "/calendar/1",
        },
    )

    assert response.status_code == 200
    assert response.json()["frequency"] == "daily"


def test_update_prescription(client, monkeypatch):
    user = _user("13131313-1313-1313-1313-131313131313", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(prescription_router, "db_update_prescription", lambda prescription: prescription.model_dump())

    response = client.put(
        f"/api/update-prescription/{user.id}",
        json={
            "patient_id": str(user.id),
            "type": "Medication",
            "description": "Take one tablet daily.",
            "frequency": "daily",
            "start_date": "2026-01-01",
            "end_date": "2026-02-01",
            "calendar_path": "/calendar/1",
        },
    )

    assert response.status_code == 200
    assert response.json()["calendar_path"] == "/calendar/1"


def test_delete_prescription(client, monkeypatch):
    user = _user("14141414-1414-1414-1414-141414141414", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(prescription_router, "db_delete_prescription", lambda patient_id: True)

    response = client.delete(f"/api/delete-prescription/{user.id}")

    assert response.status_code == 204


def test_get_prescription(client, monkeypatch):
    user = _user("15151515-1515-1515-1515-151515151515", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(
        prescription_router,
        "db_get_prescription",
        lambda patient_id: {
            "patient_id": str(patient_id),
            "type": "Medication",
            "description": "Take one tablet daily.",
            "frequency": "daily",
            "start_date": "2026-01-01",
            "end_date": "2026-02-01",
            "calendar_path": "/calendar/1",
        },
    )

    response = client.get(f"/api/get-prescription?patient_id={user.id}")

    assert response.status_code == 200
    assert response.json()["type"] == "Medication"


def test_add_vitals(client, monkeypatch):
    user = _user("16161616-1616-1616-1616-161616161616", UserRole.doctor)
    _set_current_user(user)
    monkeypatch.setattr(vitals_router, "upsert_vitals", lambda vitals: vitals.model_dump())

    response = client.post(
        "/api/add-vitals",
        json={
            "patient_id": str(user.id),
            "recorded_at": "2026-01-01T08:00:00+00:00",
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 72,
        },
    )

    assert response.status_code == 200
    assert response.json()["heart_rate"] == 72


def test_update_vitals(client, monkeypatch):
    user = _user("17171717-1717-1717-1717-171717171717", UserRole.doctor)
    _set_current_user(user)
    monkeypatch.setattr(vitals_router, "db_update_vitals", lambda vitals: vitals.model_dump())

    response = client.put(
        f"/api/update-vitals/{user.id}/2026-01-01T08:00:00+00:00",
        json={
            "patient_id": str(user.id),
            "recorded_at": "2026-01-01T08:00:00+00:00",
            "systolic_bp": 121,
            "diastolic_bp": 81,
            "heart_rate": 73,
        },
    )

    assert response.status_code == 200
    assert response.json()["systolic_bp"] == 121


def test_delete_vitals(client, monkeypatch):
    user = _user("18181818-1818-1818-1818-181818181818", UserRole.doctor)
    _set_current_user(user)
    monkeypatch.setattr(vitals_router, "db_delete_vitals", lambda patient_id, recorded_at: True)

    response = client.delete(f"/api/delete-vitals/{user.id}/2026-01-01T08:00:00+00:00")

    assert response.status_code == 204


def test_get_vitals(client, monkeypatch):
    user = _user("19191919-1919-1919-1919-191919191919", UserRole.doctor)
    _set_current_user(user)
    monkeypatch.setattr(
        vitals_router,
        "db_get_vitals",
        lambda patient_id, recorded_at: {
            "patient_id": str(patient_id),
            "recorded_at": "2026-01-01T08:00:00+00:00",
            "systolic_bp": 122,
            "diastolic_bp": 82,
            "heart_rate": 74,
        },
    )

    response = client.get(f"/api/get-vitals?patient_id={user.id}&recorded_at=2026-01-01T08:00:00+00:00")

    assert response.status_code == 200
    assert response.json()["diastolic_bp"] == 82


def test_get_vitals_history(client, monkeypatch):
    user = _user("20202020-2020-2020-2020-202020202020", UserRole.doctor)
    _set_current_user(user)
    monkeypatch.setattr(
        vitals_router,
        "db_get_vitals_history",
        lambda patient_id: [
            {
                "patient_id": str(patient_id),
                "recorded_at": "2026-01-01T08:00:00+00:00",
                "systolic_bp": 123,
            }
        ],
    )

    response = client.get(f"/api/get-vitals-history?patient_id={user.id}")

    assert response.status_code == 200
    assert response.json()[0]["systolic_bp"] == 123


def test_summarize(client, monkeypatch):
    user = _user("21212121-2121-2121-2121-212121212121", UserRole.doctor)
    _set_current_user(user)
    monkeypatch.setattr(summary_router, "get_patient_record", lambda patient_id: {"id": str(patient_id), "name": "Ada"})
    monkeypatch.setattr(summary_router, "get_vitals_history", lambda patient_id: [{"recorded_at": "2026-01-01T08:00:00+00:00"}])
    monkeypatch.setattr(summary_router, "get_patient_history", lambda patient_id: [{"occurred_at": "2026-01-01T09:00:00+00:00"}])
    monkeypatch.setattr(summary_router, "ask_gemini", lambda prompt: FakeResponse("Summary text."))

    response = client.post("/api/summarize", json={"patient_id": str(user.id)})

    assert response.status_code == 200
    assert response.json()["summary"] == "Summary text."


def test_recommend(client, monkeypatch):
    user = _user("22222222-2222-2222-2222-222222222222", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(summary_router, "get_patient_record", lambda patient_id: {"id": str(patient_id), "name": "Ada"})
    monkeypatch.setattr(summary_router, "get_vitals_history", lambda patient_id: [])
    monkeypatch.setattr(summary_router, "get_patient_history", lambda patient_id: [])
    monkeypatch.setattr(summary_router, "ask_gemini", lambda prompt: FakeResponse("- Stay hydrated."))

    response = client.get("/api/recommend")

    assert response.status_code == 200
    assert response.json()["recommendations"] == "- Stay hydrated."


def test_remind(client, monkeypatch):
    user = _user("23232323-2323-2323-2323-232323232323", UserRole.patient)
    _set_current_user(user)
    monkeypatch.setattr(summary_router, "get_patient_record", lambda patient_id: {"id": str(patient_id), "name": "Ada"})
    monkeypatch.setattr(
        summary_router,
        "get_prescription",
        lambda patient_id: {"patient_id": str(patient_id), "description": "Take one tablet daily."},
    )
    monkeypatch.setattr(summary_router, "ask_gemini", lambda prompt: FakeResponse("Take your tablet this morning."))

    response = client.get("/api/remind")

    assert response.status_code == 200
    assert response.json()["reminder"] == "Take your tablet this morning."


def test_talk(client, monkeypatch):
    user = _user("24242424-2424-2424-2424-242424242424", UserRole.patient)
    _set_current_user(user)
    recorded_messages: list[tuple[str, str, str]] = []

    monkeypatch.setattr(talk_router, "get_patient_chat_context", lambda patient_id: {"context": "ok"})
    monkeypatch.setattr(talk_router, "get_conversation_summary", lambda patient_id: "")
    monkeypatch.setattr(talk_router, "get_recent_conversation_messages", lambda patient_id, limit=8: [])
    monkeypatch.setattr(talk_router, "append_conversation_message", lambda patient_id, role, content: recorded_messages.append((str(patient_id), role, content)))
    monkeypatch.setattr(talk_router, "get_message_count", lambda patient_id: 1)
    monkeypatch.setattr(talk_router, "ask_gemini", lambda prompt: FakeResponse("I can help with that."))

    response = client.post("/api/talk", json={"message": "I feel better today."})

    assert response.status_code == 200
    assert response.json()["response"] == "I can help with that."
    assert [entry[1] for entry in recorded_messages] == ["user", "assistant"]


def test_latest_update_uses_most_recent_event():
    patient_history = [
        {"occurred_at": "2026-01-01T10:00:00+00:00"},
        {"occurred_at": "2026-01-03T09:00:00+00:00"},
    ]
    vitals_history = [
        {"recorded_at": "2026-01-02T12:00:00+00:00"},
    ]

    latest = patients_router._latest_update(patient_history, vitals_history)

    assert latest == datetime(2026, 1, 3, 9, 0, tzinfo=timezone.utc)


def test_rule_based_alert_flags_high_risk_vitals():
    alert = patients_router._rule_based_alert(
        [
            {
                "systolic_bp": 182,
                "diastolic_bp": 121,
                "heart_rate": 126,
                "temperature_c": 38.4,
                "spo2": 89,
            }
        ]
    )

    assert alert == "Active alert: critically high blood pressure, tachycardia, fever, low oxygen saturation."