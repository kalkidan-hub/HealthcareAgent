from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from backend.infrastructure.auth import ensure_doctor_access, ensure_patient_access, get_current_user
from backend.infrastructure.db_repo import get_prescription as db_get_prescription
from backend.infrastructure.db_repo import delete_prescription as db_delete_prescription
from backend.infrastructure.db_repo import update_prescription as db_update_prescription
from backend.infrastructure.db_repo import upsert_prescription
from backend.models.patient import Prescription


router = APIRouter()


@router.post("/add-prescription")
def add_prescription(prescription: Prescription, current_user=Depends(get_current_user)):
    print(prescription)
    ensure_doctor_access(current_user)
    return upsert_prescription(prescription)


@router.put("/update-prescription/{patient_id}")
def update_prescription(patient_id: UUID, prescription: Prescription, current_user=Depends(get_current_user)):
    if prescription.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id mismatch")
    ensure_patient_access(current_user, patient_id)
    data = db_update_prescription(prescription)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
    return data


@router.delete("/delete-prescription/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prescription(patient_id: UUID, current_user=Depends(get_current_user)):
    ensure_patient_access(current_user, patient_id)
    deleted = db_delete_prescription(patient_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
    return None


@router.get("/get-prescription")
def get_prescription(patient_id: UUID, current_user=Depends(get_current_user)):
    ensure_patient_access(current_user, patient_id)
    data = db_get_prescription(patient_id)
    if not data:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return Prescription.model_validate(data)