from backend.infrastructure.gemini_llm import ask_gemini
from backend.infrastructure.local_storage import get_patient_name, get_patient_risk_factors, get_prescription, save_to_local_storage
from backend.models.patient import Prescription, RiskFactor



class RiskFactorExtractorAgent:
    def __init__(self, patient_id: int):
        self.patient_id = patient_id

    def extract_risk_factors(self):
        """Extract risk factors from the explanations using gemini_llm and update the patient's record."""
        prompt = ...

        risk_factors = ask_gemini(prompt)
        
        filename = f"risk_factor/{self.patient_id}.json"
        save_to_local_storage(filename, risk_factors.model_dump_json())

class EmailCreatorAgent:
    def __init__(self, patient_id: int):
        self.patient_id = patient_id
        self.risk_factors = get_patient_risk_factors(patient_id)
        self.prescription = get_prescription(patient_id)

    def compose_email_of_riskfactors(self) -> dict:
        """Compose an email to be sent to the user."""
        user_name = get_patient_name(self.patient_id)
        prompt = f"Compose an email to {user_name} that informs them about the risk factors they are facing: {self.risk_factors}. Provide guidance on how to mitigate or manage these risk factors."

        response = ask_gemini(prompt)
        email_content = response.text.split("\n", 1)  # Split into subject and body

        email = {
            "to": user_name,
            "subject": email_content[0].replace("Subject:", "").strip(),
            "body": email_content[1].replace("Body:", "").strip()
        }

        return email
    
    def compose_email_of_prescription(self) -> dict:
        """Compose an email to be sent to the user."""
        user_name = get_patient_name(self.patient_id)
        prompt = f"Compose an email to {user_name} that insists and informs them to follow the prescription. Include the health benefits associated with the prescription: {self.prescription}."

        response = ask_gemini(prompt)
        email_content = response.text.split("\n", 1)
        email = {
            "to": user_name,
            "subject": email_content[0].replace("Subject:", "").strip(),
            "body": email_content[1].replace("Body:", "").strip()
        }
        return email

class FrequencyDeciderAgent:
    def __init__(self, patient_id: int):
        self.patient_id = patient_id
        self.risk_factors = get_patient_risk_factors(patient_id)

    def decide_frequency(self) -> str:
        """Decide the frequency of the prescription based on the risk factors."""
        prompt = f"Based on the following risk factors: {self.risk_factors}, decide the checkup frequency. The answer should be one of the following: daily, weekly, monthly, or yearly."

        response = ask_gemini(prompt)
        frequency = response.text.strip()

        return frequency