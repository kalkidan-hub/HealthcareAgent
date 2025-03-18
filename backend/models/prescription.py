from pydantic import BaseModel
from datetime import date
from typing import Optional

class Prescription(BaseModel):
    id: int
    type: str
    description: str
    patient_id: int
    frequency: str
    start_date: date
    end_date: Optional[date]

    class Config:
        orm_mode = True
