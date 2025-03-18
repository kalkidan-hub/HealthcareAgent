from fastapi import APIRouter, HTTPException
from backend.models.lab_report import LabReport
from backend.infrastructure.local_storage import save_to_local_storage
from backend.services.analyzer import analyze_report
from backend.services.risk_factor_extractor import extract_risk_factors

router = APIRouter()

@router.post("/add-lab-report")
def add_lab_report(lab_report: LabReport):
    # Save lab report to local storage
    filename = f"lab_reports/{lab_report.patient_id}_{lab_report.report_date}.json"
    save_to_local_storage(filename, lab_report.model_dump_json())

    # Analyze the lab report
    analysis_result = analyze_report(lab_report.dict(), lab_report.patient_id)

    # Extract risk factors from the analysis result
    extract_risk_factors(analysis_result["explanations"], lab_report.patient_id)
    
    # Update patient's risk factors (placeholder implementation)
    # update_patient_risk_factors(lab_report.patient_id, risk_factors)

    return {
        "message": "Lab report added and analyzed",
        "analysis_result": analysis_result,
    }