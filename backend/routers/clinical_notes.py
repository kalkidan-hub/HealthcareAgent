from fastapi import APIRouter, HTTPException
from backend.models.patient import ClinicalNote
from backend.infrastructure.local_storage import save_to_local_storage

router = APIRouter()

@router.post("/add-clinical-note")
def add_clinical_note(clinical_note: ClinicalNote):
    # Save clinical note to local storage
    filename = f"clinical_notes/{clinical_note.patient_id}_{clinical_note.note_date}.json"
    save_to_local_storage(filename, clinical_note.model_dump_json())

@router.get("/get-clinical-note")
def get_clinical_note(patient_id: str, note_date: str):
    filename = f"clinical_notes/{patient_id}_{note_date}.json"
    clinical_note = ClinicalNote.from_json(filename)
    return clinical_note