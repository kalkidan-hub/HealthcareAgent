import json

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from backend.infrastructure.auth import ensure_patient_role, get_current_user
from backend.infrastructure.db_repo import append_conversation_message
from backend.infrastructure.db_repo import get_all_conversation_messages
from backend.infrastructure.db_repo import get_patient_chat_context
from backend.infrastructure.db_repo import get_conversation_summary
from backend.infrastructure.db_repo import get_message_count
from backend.infrastructure.db_repo import get_recent_conversation_messages
from backend.infrastructure.db_repo import prune_conversation_messages
from backend.infrastructure.db_repo import set_conversation_summary
from backend.infrastructure.gemini_llm import ask_gemini
from backend.models.talk import TalkRequest, TalkResponse

router = APIRouter()

MAX_RECENT_TURNS = 8
SUMMARY_TRIGGER_MESSAGE_COUNT = 20

@router.post("/talk", response_model=TalkResponse)
async def talk(request: TalkRequest, current_user=Depends(get_current_user)):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    ensure_patient_role(current_user)

    context = get_patient_chat_context(current_user.id)
    protected_summary = get_conversation_summary(current_user.id)
    recent_messages = get_recent_conversation_messages(current_user.id, limit=MAX_RECENT_TURNS)
    context_blob = json.dumps(context, default=str, indent=2)
    conversation_blob = json.dumps(recent_messages, default=str, indent=2)
    protected_anchor_blob = protected_summary.strip()

    prompt = f"""
You are a patient-facing healthcare assistant.

Use the provided protected anchor summary, the patient context, the recent conversation transcript,
and the user's new message.

The protected anchor summary is long-term memory. Preserve it unless the new conversation clearly
adds durable facts, ongoing goals, or unresolved health concerns.

Be helpful, concise, and clinically cautious.
Do not claim to be a doctor. If symptoms sound urgent or unsafe, advise the patient to seek urgent medical care.
When relevant, refer to the patient's past prescriptions, lab reports, and clinical notes.

Protected anchor summary:
{protected_anchor_blob or "(none yet)"}

Recent conversation:
{conversation_blob}

Patient context:
{context_blob}

Patient message:
{request.message.strip()}

Respond directly to the patient in plain language.
""".strip()

    try:
        append_conversation_message(current_user.id, "user", request.message.strip())
        response = await run_in_threadpool(ask_gemini, prompt)
        response_text = getattr(response, "text", str(response)).strip()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc

    if not response_text:
        raise HTTPException(status_code=502, detail="Gemini returned an empty response")

    append_conversation_message(current_user.id, "assistant", response_text)

    message_count = get_message_count(current_user.id)
    if message_count > SUMMARY_TRIGGER_MESSAGE_COUNT:
        all_messages = get_all_conversation_messages(current_user.id)
        older_messages = all_messages[:-MAX_RECENT_TURNS] if len(all_messages) > MAX_RECENT_TURNS else []
        older_blob = json.dumps(older_messages, default=str, indent=2)
        summary_prompt = f"""
You are compressing a patient conversation into a protected anchor summary.

Rules:
- Preserve durable facts, ongoing symptoms, medications, risks, preferences, and unresolved questions.
- Do not include unnecessary word-for-word dialogue.
- Do not invent facts.
- Keep the result concise and clinically useful.

Existing protected anchor summary:
{protected_anchor_blob or "(none yet)"}

Patient context:
{context_blob}

Older conversation to compress:
{older_blob or "(none)"}

Write an updated protected anchor summary.
""".strip()

        try:
            summary_response = await run_in_threadpool(ask_gemini, summary_prompt)
            summary_text = getattr(summary_response, "text", str(summary_response)).strip()
            if summary_text:
                set_conversation_summary(current_user.id, summary_text)
                prune_conversation_messages(current_user.id, keep_last=MAX_RECENT_TURNS)
        except Exception:
            # Keep the chat usable even if summarization fails; the raw recent turns remain available.
            pass

    return TalkResponse(response=response_text)