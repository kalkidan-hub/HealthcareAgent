from pydantic import BaseModel, EmailStr
from typing import List

class PatientModel(BaseModel):
    id: int
    name: str
    age: int
    email: EmailStr
    risk_factors: List[str]

    class Config:
        orm_mode = True