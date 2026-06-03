import json
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from backend.infrastructure.auth import ensure_doctor_access, get_current_user
from backend.infrastructure.db_repo import (
    get_all_patient_records,
    get_clinical_note_history,
    get_patient_history,
    get_vitals_history,
)
from backend.infrastructure.gemini_llm import ask_gemini
from backend.models.patients import PatientInfo, PatientListItem, PatientListResponse


router = APIRouter()


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _latest_update(patient_history: list[dict], vitals_history: list[dict]) -> datetime | None:
    candidates: list[datetime] = []

    for event in patient_history:
        parsed = _parse_datetime(event.get("occurred_at"))
        if parsed is not None:
            candidates.append(parsed)

    for vital in vitals_history:
        parsed = _parse_datetime(vital.get("recorded_at"))
        if parsed is not None:
            candidates.append(parsed)

    if not candidates:
        return None
    return max(candidates)


async def _extract_chief_complaint(clinical_notes: list[dict]) -> str:
    if not clinical_notes:
        return "No documented chief complaint."

    notes_blob = json.dumps(clinical_notes, default=str, indent=2)
    prompt = f"""
Extract the patient's chief complaint from these clinical notes.

Rules:
- Return one short sentence only.
- Focus on the main complaint or primary ongoing concern.
- If unclear, return: Chief complaint not clearly documented.
- Do not invent facts.

Clinical notes:
{notes_blob}
""".strip()

    try:
        response = await run_in_threadpool(ask_gemini, prompt)
        text = getattr(response, "text", str(response)).strip()
        return text or "Chief complaint not clearly documented."
    except Exception:
        latest_note = str(clinical_notes[0].get("note", "")).strip()
        if not latest_note:
            return "Chief complaint not clearly documented."
        return latest_note.split("\n", 1)[0][:180]


def _rule_based_alert(vitals_history: list[dict]) -> str:
    if not vitals_history:
        return "No active alert from documented vitals."

    latest = vitals_history[0]
    alerts: list[str] = []

    systolic = latest.get("systolic_bp")
    diastolic = latest.get("diastolic_bp")
    heart_rate = latest.get("heart_rate")
    temperature_c = latest.get("temperature_c")
    spo2 = latest.get("spo2")

    if isinstance(systolic, int) and isinstance(diastolic, int):
        if systolic >= 180 or diastolic >= 120:
            alerts.append("critically high blood pressure")
        elif systolic >= 140 or diastolic >= 90:
            alerts.append("elevated blood pressure")

    if isinstance(heart_rate, int):
        if heart_rate > 120:
            alerts.append("tachycardia")
        elif heart_rate < 50:
            alerts.append("bradycardia")

    if isinstance(temperature_c, (int, float)) and temperature_c >= 38:
        alerts.append("fever")

    if isinstance(spo2, int) and spo2 < 92:
        alerts.append("low oxygen saturation")

    if not alerts:
        return "No active alert from latest documented vitals."
    return "Active alert: " + ", ".join(alerts) + "."


async def _extract_active_alert(vitals_history: list[dict]) -> str:
    if not vitals_history:
        return "No active alert from documented vitals."

    vitals_blob = json.dumps(vitals_history, default=str, indent=2)
    prompt = f"""
Review these vitals and extract one active alert for a doctor handoff.

Rules:
- Return one short sentence.
- Mention the most clinically important current alert only.
- If no concerning pattern is present, return: No active alert from documented vitals.
- Do not invent facts.

Vitals:
{vitals_blob}
""".strip()

    try:
        response = await run_in_threadpool(ask_gemini, prompt)
        text = getattr(response, "text", str(response)).strip()
        return text or _rule_based_alert(vitals_history)
    except Exception:
        return _rule_based_alert(vitals_history)


@router.get("/patients", response_model=PatientListResponse)
async def list_patients(current_user=Depends(get_current_user)):
    ensure_doctor_access(current_user)

    patients = get_all_patient_records()
    items: list[PatientListItem] = []

    for patient in patients:
        patient_id = patient.get("id")
        if not patient_id:
            continue

        clinical_notes = get_clinical_note_history(patient_id)
        vitals_history = get_vitals_history(patient_id)
        patient_history = get_patient_history(patient_id)

        chief_complaint = await _extract_chief_complaint(clinical_notes)
        active_alert = await _extract_active_alert(vitals_history)
        last_update = _latest_update(patient_history, vitals_history)

        items.append(
            PatientListItem(
                patient_id=patient_id,
                name=patient.get("name") or "",
                info=PatientInfo(sex=patient.get("sex"), age=patient.get("age")),
                chief_complaint=chief_complaint,
                active_alert=active_alert,
                last_update=last_update,
            )
        )

    return PatientListResponse(items=items)
