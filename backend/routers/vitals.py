from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from uuid import UUID

from backend.infrastructure.auth import ensure_doctor_access, get_current_user
from backend.infrastructure.db_repo import delete_vitals as db_delete_vitals
from backend.infrastructure.db_repo import get_vitals as db_get_vitals
from backend.infrastructure.db_repo import get_vitals_history as db_get_vitals_history
from backend.infrastructure.db_repo import update_vitals as db_update_vitals
from backend.infrastructure.db_repo import upsert_vitals
from backend.models.patient import Vitals


router = APIRouter()


def _normalize_recorded_at(value: str | datetime) -> str:
    if isinstance(value, datetime):
        recorded_at = value
    else:
        try:
            recorded_at = datetime.fromisoformat(value)
        except ValueError:
            return value.strip()
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)
    return recorded_at.astimezone(timezone.utc).isoformat()


@router.post("/add-vitals")
def add_vitals(vitals: Vitals, current_user=Depends(get_current_user)):
    ensure_doctor_access(current_user)
    return upsert_vitals(vitals)


@router.put("/update-vitals/{patient_id}/{recorded_at}")
def update_vitals(patient_id: UUID, recorded_at: str, vitals: Vitals, current_user=Depends(get_current_user)):
    ensure_doctor_access(current_user)
    if vitals.patient_id != patient_id or _normalize_recorded_at(vitals.recorded_at) != _normalize_recorded_at(recorded_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id or recorded_at mismatch")
    data = db_update_vitals(vitals)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vitals not found")
    return data


@router.delete("/delete-vitals/{patient_id}/{recorded_at}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vitals(patient_id: UUID, recorded_at: str, current_user=Depends(get_current_user)):
    ensure_doctor_access(current_user)
    deleted = db_delete_vitals(patient_id, recorded_at)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vitals not found")
    return None


@router.get("/get-vitals")
def get_vitals(patient_id: UUID, recorded_at: str, current_user=Depends(get_current_user)):
    ensure_doctor_access(current_user)
    data = db_get_vitals(patient_id, recorded_at)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vitals not found")
    return Vitals.model_validate(data)


@router.get("/get-vitals-history")
def get_vitals_history(patient_id: UUID, current_user=Depends(get_current_user)):
    ensure_doctor_access(current_user)
    return [Vitals.model_validate(item) for item in db_get_vitals_history(patient_id)]