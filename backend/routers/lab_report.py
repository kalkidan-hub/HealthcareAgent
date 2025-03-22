import json
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
    filename = f"local_storage/lab_reports/{patient_id}_{report_date}.json"
    try:
        with open(filename, 'r') as file:
            lab_report_data = json.load(file)
        lab_report = LabReport.parse_obj(lab_report_data)
        return lab_report
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Lab report not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Error decoding JSON")