import json
from fastapi import APIRouter, HTTPException
from backend.models.patient import ClinicalNote
from backend.infrastructure.local_storage import save_to_local_storage

router = APIRouter()

@router.post("/add-clinical-note")
def add_clinical_note(clinical_note: ClinicalNote):
    # Save clinical note to local storage
    filename = f"clinical_notes/{clinical_note.patient_id}.json"
    save_to_local_storage(filename, clinical_note.dict())

@router.get("/get-clinical-note")
def get_clinical_note(patient_id: str):
    filename = f"local_storage/clinical_notes/{patient_id}.json"
    try:
        with open(filename, 'r') as file:
            clinical_note_data = json.load(file)
        clinical_note = ClinicalNote.parse_obj(clinical_note_data)
        return clinical_note
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Clinical note not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Error decoding JSON")