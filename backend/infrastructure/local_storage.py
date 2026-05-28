import os
import json
from typing import Optional

from backend.infrastructure.db_repo import (
    get_email as db_get_email,
    get_patient_name as db_get_patient_name,
    get_patient_record,
    get_patient_risk_factors as db_get_patient_risk_factors,
    get_prescription as db_get_prescription,
    update_patient_risk_factors as db_update_patient_risk_factors,
)
from backend.models.patient import PatientModel, Prescription

BASE_DIR = "local_storage"

def save_to_local_storage(filename: str, content):
    """Saves JSON content to the local filesystem.

    Accepts either a Python object (dict/list) or a JSON string. If a JSON
    string is provided, it will be parsed and written as JSON so that
    consumers reading the file get a JSON object instead of a quoted string.
    """
    file_path = os.path.join(BASE_DIR, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Normalize content: if it's a JSON string, parse it first
    to_write = content
    if isinstance(content, str):
        try:
            to_write = json.loads(content)
        except json.JSONDecodeError:
            # Not a JSON string — write raw text
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            return file_path

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(to_write, file)
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
    return get_patient_record(user_id)

def update_patient_risk_factors(patient_id: int, risk_factors: str):
    """Update the patient's risk factors."""
    return db_update_patient_risk_factors(patient_id, risk_factors)


def get_patient_name(user_id: int) -> str:
    """Retrieve the patient's name from local storage."""
    return db_get_patient_name(user_id)
    

def get_patient_risk_factors(patient_id: int) -> list:
    """Retrieve the patient's risk factors from local storage."""
    return db_get_patient_risk_factors(patient_id)

def get_prescription(patient_id: int) -> dict:
    """Retrieve the patient's prescription from local storage."""
    return db_get_prescription(patient_id)

def get_calendar_path(patient_id: int) -> Optional[str]:
    """Retrieve the calendar path from the patient's prescription."""
    prescription_data = get_prescription(patient_id)
    if prescription_data:
        prescription = Prescription(**prescription_data)
        return prescription.calendar_path
    return None

def get_email(patient_id: int) -> str:
    """Retrieve the patient's email from local storage."""
    return db_get_email(patient_id)
