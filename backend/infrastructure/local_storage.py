import os
import json

BASE_DIR = "local_storage"

def save_to_local_storage(filename: str, content: str):
    """Saves a JSON object to the local filesystem."""
    file_path = os.path.join(BASE_DIR, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as file:
        json.dump(content, file)
    return file_path

def load_from_local_storage(filename: str) -> str:
    """Loads a string content from the local filesystem."""
    file_path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{filename} not found in local storage.")
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def get_patient_by_id(user_id: int) -> dict:
    """Get user data by user ID."""

    filename = f"users/{user_id}.json"
    try:
        return json.loads(load_from_local_storage(filename))
    except FileNotFoundError:
        return None

def update_patient_risk_factors(patient_id: int, risk_factors: str):
    """Update the patient's risk factors."""
    patient = get_patient_by_id(patient_id)
    patient["risk_factors"] = risk_factors
    filename = f"patients/{patient_id}.json"
    save_to_local_storage(filename, patient)


def get_patient_name(user_id: int) -> str:
    """Retrieve the patient's name from local storage."""
    patient = get_patient_by_id(user_id)
    if patient:
        return patient.get("name", "User")
    return "User"

def get_patient_risk_factors(patient_id: int) -> list:
    """Retrieve the patient's risk factors from local storage."""
    patient = get_patient_by_id(patient_id)
    if patient:
        return patient.get("risk_factors", [])
    return []