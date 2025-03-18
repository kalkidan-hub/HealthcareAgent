from backend.infrastructure.gemini_llm import ask_gemini
from backend.infrastructure.local_storage import load_from_local_storage


def analyze_report(report_data: dict, patient_id:int) -> dict:
    """Analyze the lab report and return possible explanations and suggested actions."""
    # Retrieve the current prescription and recent conversation from local storage
    prescription_filename = f"prescriptions/{patient_id}.json"
    conversation_filename = f"conversations/{patient_id}.txt"

    try:
        prescription = load_from_local_storage(prescription_filename)
    except FileNotFoundError:
        prescription = {}

    try:
        with open(conversation_filename, 'r') as file:
            recent_conversation = file.read()
    except FileNotFoundError:
        recent_conversation = ""

    prompt = f"""
    Analyze the following lab report, prescription, and recent conversation to provide possible explanations and suggested actions.

    Lab Report:
    {report_data}

    Prescription:
    {prescription}

    Recent Conversation:
    {recent_conversation}

    Provide detailed explanations for the analysis you make.
    """

    explain_response = ask_gemini(prompt)
    suggestion_prompt = f"""
    Based on the analysis{explain_response.text}, provide suggested actions for the patient.
    """
    suggestion_response = ask_gemini(suggestion_prompt)

    analysis_result = {
        "explanations": explain_response.text,
        "suggested_actions": suggestion_response.text
    }

    return analysis_result