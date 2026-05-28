from fastapi import APIRouter, HTTPException, status

from backend.infrastructure.db_repo import get_lab_report as db_get_lab_report
from backend.infrastructure.db_repo import delete_lab_report as db_delete_lab_report
from backend.infrastructure.db_repo import update_lab_report as db_update_lab_report
from backend.infrastructure.db_repo import upsert_lab_report
from backend.models.patient import LabReport

router = APIRouter()

@router.post("/add-lab-report")
def add_lab_report(lab_report: LabReport):
    return upsert_lab_report(lab_report)


@router.put("/update-lab-report/{patient_id}/{report_date}")
def update_lab_report(patient_id: int, report_date: str, lab_report: LabReport):
    if lab_report.patient_id != patient_id or lab_report.report_date != report_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id or report_date mismatch")
    data = db_update_lab_report(lab_report)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab report not found")
    return data


@router.delete("/delete-lab-report/{patient_id}/{report_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lab_report(patient_id: int, report_date: str):
    deleted = db_delete_lab_report(patient_id, report_date)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab report not found")
    return None

@router.get("/get-lab-report")
def get_lab_report(patient_id: int, report_date: str):
    data = db_get_lab_report(patient_id, report_date)
    if not data:
        raise HTTPException(status_code=404, detail="Lab report not found")
    return LabReport.model_validate(data)