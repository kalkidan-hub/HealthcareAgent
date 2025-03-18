import datetime
from pydantic import BaseModel
from typing import Optional

class LabReport(BaseModel):
    id: int
    name: str
    patient_id: int
    type: str
    report_date: str
    result_value: float
    unit: str
    normal_range: str
    status: str