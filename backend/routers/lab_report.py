from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from backend.infrastructure.auth import ensure_doctor_access, ensure_patient_access, get_current_user
from backend.infrastructure.db_repo import get_lab_report as db_get_lab_report
from backend.infrastructure.db_repo import delete_lab_report as db_delete_lab_report
from backend.infrastructure.db_repo import update_lab_report as db_update_lab_report
from backend.infrastructure.db_repo import upsert_lab_report
from backend.models.patient import LabReport

router = APIRouter()


def _normalize_report_date(value: str | datetime) -> str:
    if isinstance(value, datetime):
        report_date = value
    else:
        try:
            report_date = datetime.fromisoformat(value)
        except ValueError:
            return value.strip()
    if report_date.tzinfo is None:
        report_date = report_date.replace(tzinfo=timezone.utc)
    return report_date.astimezone(timezone.utc).isoformat()

@router.post("/add-lab-report")
def add_lab_report(lab_report: LabReport, current_user=Depends(get_current_user)):
    ensure_doctor_access(current_user)
    return upsert_lab_report(lab_report)


@router.put("/update-lab-report/{patient_id}/{report_date}")
def update_lab_report(patient_id: UUID, report_date: str, lab_report: LabReport, current_user=Depends(get_current_user)):
    if lab_report.patient_id != patient_id or _normalize_report_date(lab_report.report_date) != _normalize_report_date(report_date):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id or report_date mismatch")
    ensure_patient_access(current_user, patient_id)
    data = db_update_lab_report(lab_report)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab report not found")
    return data


@router.delete("/delete-lab-report/{patient_id}/{report_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lab_report(patient_id: UUID, report_date: str, current_user=Depends(get_current_user)):
    ensure_patient_access(current_user, patient_id)
    deleted = db_delete_lab_report(patient_id, report_date)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab report not found")
    return None

@router.get("/get-lab-report")
def get_lab_report(patient_id: UUID, report_date: str, current_user=Depends(get_current_user)):
    ensure_patient_access(current_user, patient_id)
    data = db_get_lab_report(patient_id, report_date)
    if not data:
        raise HTTPException(status_code=404, detail="Lab report not found")
    return LabReport.model_validate(data)