from uuid import UUID

from pydantic import BaseModel


class SummarizeRequest(BaseModel):
    patient_id: UUID


class SummarizeResponse(BaseModel):
    patient_id: UUID
    summary: str