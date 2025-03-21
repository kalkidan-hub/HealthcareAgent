from datetime import date
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from schedule import Job

# inspired by EHRS

class Demography(BaseModel):
    id: int
    patient_id: int
    name: str
    age: int
    email: EmailStr

class Prescription(BaseModel):
    id: int
    patient_id: int
    type: str
    description: str
    frequency: str
    start_date: date
    end_date: Optional[date]
    calendar_path: str

    class Config:
        orm_mode = True

class LabReport(BaseModel):
    id: int
    patient_id: int
    name: str
    type: str
    report_date: str
    result_value: float
    unit: str
    normal_range: str
    status: str

class CinicalNotes(BaseModel):
    id: int
    patient_id: int
    note: str

class PatientModel(BaseModel):
    id: int
    Demography: Demography
    prescriptions: List[Prescription]
    lab_reports: List[LabReport]
    clinical_notes: List[CinicalNotes]


class RiskFactor(BaseModel):
    id: int
    patient_id: int
    risk_factor: str
    description: str

class EmailCheckup(BaseModel):
    id: int
    patient_id: int
    frequency: str
    job: Job
