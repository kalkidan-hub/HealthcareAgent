from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional

from schedule import Job

# inspired by EHRS

class Demography(BaseModel):
    id: int
    patient_id: UUID
    name: str
    age: int
    email: EmailStr

class Prescription(BaseModel):
    id: int
    patient_id: UUID
    type: str
    description: str
    frequency: str
    start_date: date
    end_date: Optional[date]
    calendar_path: str

    model_config = ConfigDict(from_attributes=True)

class LabReport(BaseModel):
    id: int
    patient_id: UUID
    name: str
    type: str
    report_date: str
    result_value: float
    unit: str
    normal_range: str
    status: str

class ClinicalNote(BaseModel):
    id: int
    patient_id: UUID
    note: str

class PatientModel(BaseModel):
    id: UUID
    Demography: Demography
    prescriptions: List[Prescription]
    lab_reports: List[LabReport]
    clinical_notes: List[ClinicalNote]


class RiskFactor(BaseModel):
    id: int
    patient_id: UUID
    risk_factor: str
    description: str

class EmailCheckup(BaseModel):
    id: int
    patient_id: UUID
    frequency: str
    job: Job

    model_config = ConfigDict(arbitrary_types_allowed=True)
