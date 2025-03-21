from fastapi import APIRouter, HTTPException
from backend.models.patient import LabReport
from backend.infrastructure.local_storage import save_to_local_storage

router = APIRouter()

@router.post("/add-lab-report")
def add_lab_report(lab_report: LabReport):
    # Save lab report to local storage
    filename = f"lab_reports/{lab_report.patient_id}_{lab_report.report_date}.json"
    save_to_local_storage(filename, lab_report.model_dump_json())

@router.get("get_lab_report")
def get_lab_report(patient_id: str, report_date: str):
    filename = f"lab_reports/{patient_id}_{report_date}.json"
    lab_report = LabReport.from_json(filename)
    return lab_report