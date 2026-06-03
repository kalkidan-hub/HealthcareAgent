from enum import Enum
from datetime import datetime
from uuid import UUID

from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    patient = "patient"
    doctor = "doctor"


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole = UserRole.patient
    age: int | None = Field(default=None, ge=0)
    sex: str | None = Field(default=None, min_length=1)
    contact_number: str | None = Field(default=None, min_length=1)
    emergency_number: str | None = Field(default=None, min_length=1)


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    email: EmailStr | None = None
    age: int | None = Field(default=None, ge=0)
    sex: str | None = Field(default=None, min_length=1)
    contact_number: str | None = Field(default=None, min_length=1)
    emergency_number: str | None = Field(default=None, min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CurrentUser(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: UserRole
    age: int | None = None
    sex: str | None = None
    contact_number: str | None = None
    emergency_number: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientHistoryItem(BaseModel):
    event_type: str
    occurred_at: datetime
    payload: dict[str, Any]


class PatientHistoryResponse(BaseModel):
    items: list[PatientHistoryItem]


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: CurrentUser