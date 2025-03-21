import os
import json
from typing import Optional

from backend.models.patient import PatientModel, Prescription

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
    


def get_patient_name(user_id: int) -> str:
    """Retrieve the patient's name from local storage."""
    patient = get_patient_by_id(user_id) # patient is a json object
    if patient:
        return patient.get("name", "")
    

def get_patient_risk_factors(patient_id: int) -> list:
    """Retrieve the patient's risk factors from local storage."""
    patient = get_patient_by_id(patient_id)
    if patient:
        return patient.get("risk_factors", [])
    return []

def get_prescription(patient_id: int) -> dict:
    """Retrieve the patient's prescription from local storage."""
    filename = f"prescriptions/{patient_id}.json"
    try:
        return json.loads(load_from_local_storage(filename))
    except FileNotFoundError:
        return {}

def get_calendar_path(patient_id: int) -> Optional[str]:
    """Retrieve the calendar path from the patient's prescription."""
    prescription_data = get_prescription(patient_id)
    if prescription_data:
        prescription = Prescription(**prescription_data)
        return prescription.calendar_path
    return None

def get_email(patient_id: int) -> str:
    """Retrieve the patient's email from local storage."""
    patient_data = get_patient_by_id(patient_id)
    if patient_data:
        patient = PatientModel(**patient_data)
        return patient.Demography.email
    return ""
