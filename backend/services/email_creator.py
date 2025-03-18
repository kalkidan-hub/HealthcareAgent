from backend.infrastructure.gemini_llm import ask_gemini
from backend.infrastructure.local_storage import get_patient_name, get_patient_risk_factors


def compose_email(user_id: int, risk_factors: list) -> dict:
    """Compose an email to be sent to the user."""
    user_name = get_patient_name(user_id)
    risk_factor = get_patient_risk_factors(user_id)
    prompt = f"""
    Compose an email to a user named {user_name}. The subject of the email should be about {risk_factor}. The body of the email should include some awareness about the issue and things the user could do to mitigate the risk.

    Subject:
    Body:
    """

    response = ask_gemini(prompt)
    email_content = response.text.split("\n", 1)  # Split into subject and body

    email = {
        "to": user_name,
        "subject": email_content[0].replace("Subject:", "").strip(),
        "body": email_content[1].replace("Body:", "").strip()
    }

    return email