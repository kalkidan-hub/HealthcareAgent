from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PatientInfo(BaseModel):
    sex: str | None = None
    age: int | None = None


class PatientListItem(BaseModel):
    patient_id: UUID
    name: str
    info: PatientInfo
    chief_complaint: str
    active_alert: str
    last_update: datetime | None = None


class PatientListResponse(BaseModel):
    items: list[PatientListItem]
