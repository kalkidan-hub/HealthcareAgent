from backend.infrastructure.gemini_llm import ask_gemini
from backend.infrastructure.local_storage import get_patient_by_id, update_patient_risk_factors


def extract_risk_factors(explanations: str, patient_id: int) -> list:
    """Extract risk factors from the explanations using gemini_llm and update the patient's record."""
    prompt = f"""
    Based on the following explanations, extract the risk factors for the patient.

    Explanations:
    {explanations}

    Provide a list of risk factors.

    If no risk factors are identified, respond empty list."
    """

    risk_factors = ask_gemini(prompt)
    
    patient = get_patient_by_id(patient_id)
    if patient:
        update_patient_risk_factors(patient_id, risk_factors.text)
    
    