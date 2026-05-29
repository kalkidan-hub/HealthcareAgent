import json

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from backend.infrastructure.auth import ensure_doctor_access, get_current_user
from backend.infrastructure.db_repo import get_patient_history
from backend.infrastructure.db_repo import get_patient_record
from backend.infrastructure.db_repo import get_vitals_history
from backend.infrastructure.gemini_llm import ask_gemini
from backend.models.summary import SummarizeRequest, SummarizeResponse


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