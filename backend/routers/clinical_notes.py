from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from backend.infrastructure.auth import ensure_doctor_access, ensure_patient_access, get_current_user
from backend.infrastructure.db_repo import get_clinical_note as db_get_clinical_note
from backend.infrastructure.db_repo import delete_clinical_note as db_delete_clinical_note
from backend.infrastructure.db_repo import update_clinical_note as db_update_clinical_note
from backend.infrastructure.db_repo import upsert_clinical_note
from backend.models.patient import ClinicalNote

router = APIRouter()

@router.post("/add-clinical-note")
def add_clinical_note(clinical_note: ClinicalNote, current_user=Depends(get_current_user)):
    ensure_doctor_access(current_user)
    return upsert_clinical_note(clinical_note)


@router.put("/update-clinical-note/{patient_id}")
def update_clinical_note(patient_id: UUID, clinical_note: ClinicalNote, current_user=Depends(get_current_user)):
    if clinical_note.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id mismatch")
    ensure_patient_access(current_user, patient_id)
    data = db_update_clinical_note(clinical_note)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical note not found")
    return data


@router.delete("/delete-clinical-note/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clinical_note(patient_id: UUID, current_user=Depends(get_current_user)):
    ensure_patient_access(current_user, patient_id)
    deleted = db_delete_clinical_note(patient_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical note not found")
    return None

@router.get("/get-clinical-note")
def get_clinical_note(patient_id: UUID, current_user=Depends(get_current_user)):
    ensure_patient_access(current_user, patient_id)
    data = db_get_clinical_note(patient_id)
    if not data:
        raise HTTPException(status_code=404, detail="Clinical note not found")
    return ClinicalNote.model_validate(data)