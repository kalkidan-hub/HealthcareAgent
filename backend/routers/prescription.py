from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
from urllib.parse import quote


from backend.models.prescription import Prescription
from backend.services.calendar import create_ics_file
from backend.infrastructure.local_storage import save_to_local_storage

load_dotenv()

router = APIRouter()

@router.post("/add-prescription")
def add_prescription(prescription: Prescription):
    # Save prescription to local storage
    filename = f"prescriptions/{prescription.patient_id}.json"
    save_to_local_storage(filename, prescription.model_dump_json())

    ics_data = create_ics_file(prescription.type, prescription.description, prescription.start_date, prescription.end_date)

    filename = f"{quote(prescription.type)}.ics"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": "text/calendar",
    }

    return Response(content=ics_data, headers=headers, media_type="text/calendar")
