import json

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from backend.infrastructure.auth import ensure_doctor_access, ensure_patient_role, get_current_user
from backend.infrastructure.db_repo import get_patient_history
from backend.infrastructure.db_repo import get_patient_record
from backend.infrastructure.db_repo import get_prescription
from backend.infrastructure.db_repo import get_vitals_history
from backend.infrastructure.gemini_llm import ask_gemini
from backend.models.summary import RecommendResponse, SummarizeRequest, SummarizeResponse
from backend.models.summary import RemindResponse


router = APIRouter()


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest, current_user=Depends(get_current_user)):
    ensure_doctor_access(current_user)

    patient = get_patient_record(request.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    vitals_history = get_vitals_history(request.patient_id)
    patient_history = get_patient_history(request.patient_id)

    patient_blob = json.dumps(patient, default=str, indent=2)
    vitals_blob = json.dumps(vitals_history, default=str, indent=2)
    history_blob = json.dumps(patient_history, default=str, indent=2)

    prompt = f"""
You are a clinical summarization assistant for doctors.

Using the patient profile, recorded vitals, and patient history below, write a comprehensive and clinically useful summary.

Requirements:
- Focus on current status, trends, risks, and notable events.
- Highlight abnormal vitals, worsening patterns, medication or adherence concerns, and important recent events.
- Include missing information that a doctor may want to verify.
- Do not invent facts. If something is not present, say it is not documented.
- Keep it concise but comprehensive and suitable for a doctor's review.

Patient profile:
{patient_blob}

Recorded vitals:
{vitals_blob or "(none documented)"}

Patient history:
{history_blob or "(none documented)"}

Write the summary in clear medical language with short sections or bullet points.
""".strip()

    try:
        response = await run_in_threadpool(ask_gemini, prompt)
        summary_text = getattr(response, "text", str(response)).strip()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc

    if not summary_text:
        raise HTTPException(status_code=502, detail="Gemini returned an empty response")

    return SummarizeResponse(patient_id=request.patient_id, summary=summary_text)


@router.get("/recommend", response_model=RecommendResponse)
async def recommend(current_user=Depends(get_current_user)):
    ensure_patient_role(current_user)

    patient = get_patient_record(current_user.id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    vitals_history = get_vitals_history(current_user.id)
    patient_history = get_patient_history(current_user.id)

    patient_blob = json.dumps(patient, default=str, indent=2)
    vitals_blob = json.dumps(vitals_history, default=str, indent=2)
    history_blob = json.dumps(patient_history, default=str, indent=2)

    prompt = f"""
You are a patient-facing health coach for a healthcare app.

Using the patient profile, recorded vitals, and patient history below, provide brief, concise, and helpful health recommendations.

Requirements:
- Keep it short and practical.
- Focus on the most important actions, warning signs, and follow-up reminders.
- Do not diagnose or invent facts.
- If anything looks urgent or unsafe, say to seek urgent medical care.
- Use plain language a patient can understand.

Patient profile:
{patient_blob}

Recorded vitals:
{vitals_blob or "(none documented)"}

Patient history:
{history_blob or "(none documented)"}

Return the recommendations in 3 to 6 short bullet points.
""".strip()

    try:
        response = await run_in_threadpool(ask_gemini, prompt)
        recommendations_text = getattr(response, "text", str(response)).strip()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc

    if not recommendations_text:
        raise HTTPException(status_code=502, detail="Gemini returned an empty response")

    return RecommendResponse(patient_id=current_user.id, recommendations=recommendations_text)


@router.get("/remind", response_model=RemindResponse)
async def remind(current_user=Depends(get_current_user)):
    ensure_patient_role(current_user)

    patient = get_patient_record(current_user.id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    prescription = get_prescription(current_user.id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    patient_blob = json.dumps(patient, default=str, indent=2)
    prescription_blob = json.dumps(prescription, default=str, indent=2)

    prompt = f"""
You are a patient-facing medication reminder assistant.

Using the patient's profile and their current prescription below, write a brief, natural-language reminder.

Requirements:
- Keep it realistic, friendly, and concise.
- State what the patient should take or do, how often, and until when if an end date is present.
- If the prescription is a daily pill, say to take it once a day until the interval ends.
- If an end date is not present, say to keep taking it as prescribed until the doctor says otherwise.
- Do not invent medication names, doses, or instructions that are not present.
- Mention any important caution or follow-up only if it is supported by the prescription data.

Patient profile:
{patient_blob}

Current prescription:
{prescription_blob}

Write a single short reminder paragraph.
""".strip()

    try:
        response = await run_in_threadpool(ask_gemini, prompt)
        reminder_text = getattr(response, "text", str(response)).strip()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc

    if not reminder_text:
        raise HTTPException(status_code=502, detail="Gemini returned an empty response")

    return RemindResponse(patient_id=current_user.id, reminder=reminder_text)