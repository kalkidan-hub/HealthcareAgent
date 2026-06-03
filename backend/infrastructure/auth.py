from uuid import UUID

from fastapi import Header, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.infrastructure.db_repo import get_user_by_access_token
from backend.models.auth import CurrentUser, UserRole


# Security scheme used by OpenAPI/Swagger UI
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


def _extract_access_token(authorization: str | None) -> str | None:
    if not authorization:
        return None

    value = authorization.strip()
    if not value:
        return None

    if value.lower().startswith("bearer "):
        return value.split(" ", 1)[1].strip() or None

    return value


def get_current_user(
    authorization: str | None = Header(default=None),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials if credentials and credentials.credentials else _extract_access_token(authorization)

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    user_data = get_user_by_access_token(token)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return CurrentUser.model_validate(user_data)


def ensure_patient_access(current_user: CurrentUser, patient_id: UUID) -> None:
    if current_user.role == UserRole.doctor:
        return
    if current_user.id != patient_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only access your own records")


def ensure_doctor_access(current_user: CurrentUser) -> None:
    if current_user.role != UserRole.doctor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor access required")


def ensure_patient_role(current_user: CurrentUser) -> None:
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient access required")