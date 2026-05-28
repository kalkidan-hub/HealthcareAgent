from enum import Enum
from uuid import UUID

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


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CurrentUser(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: UserRole
    age: int | None = None

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: CurrentUser