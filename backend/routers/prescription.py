from fastapi import APIRouter, HTTPException, status

from backend.infrastructure.db_repo import get_prescription as db_get_prescription
from backend.infrastructure.db_repo import delete_prescription as db_delete_prescription
from backend.infrastructure.db_repo import update_prescription as db_update_prescription
from backend.infrastructure.db_repo import upsert_prescription
from backend.models.patient import Prescription


router = APIRouter()


@router.post("/add-prescription")
def add_prescription(prescription: Prescription):
    return upsert_prescription(prescription)


@router.put("/update-prescription/{patient_id}")
def update_prescription(patient_id: int, prescription: Prescription):
    if prescription.patient_id != patient_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id mismatch")
    data = db_update_prescription(prescription)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
    return data


@router.delete("/delete-prescription/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prescription(patient_id: int):
    deleted = db_delete_prescription(patient_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
    return None


@router.get("/get-prescription")
def get_prescription(patient_id: int):
    data = db_get_prescription(patient_id)
    if not data:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return Prescription.model_validate(data)