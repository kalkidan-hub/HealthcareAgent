from fastapi import APIRouter
from dotenv import load_dotenv


from backend.models.patient import Prescription
from backend.services.calendar import create_ics_file
from backend.infrastructure.local_storage import save_to_local_storage


router = APIRouter()

@router.post("/add-prescription")
def add_prescription(prescription: Prescription):
    # Save prescription to local storage
    filename = f"prescriptions/{prescription.patient_id}.json"
    save_to_local_storage(filename, prescription.model_dump_json())

@router.get("/get-prescription")
def get_prescription(patient_id: str):
    filename = f"local_storage/prescriptions/{patient_id}.json"
    prescription = Prescription.parse_file(filename)
    return prescription