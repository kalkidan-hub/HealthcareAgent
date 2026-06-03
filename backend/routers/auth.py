from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.infrastructure.auth import ensure_doctor_access, get_current_user
from backend.infrastructure.db_repo import (
    authenticate_user,
    create_access_token,
    create_user_account,
    get_patient_history,
    upsert_patient_profile,
)
from backend.models.auth import (
    AuthResponse,
    CurrentUser,
    LoginRequest,
    PatientHistoryResponse,
    RegisterRequest,
    UpdateProfileRequest,
)


router = APIRouter()


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    try:
        user = create_user_account(
            name=request.name,
            email=request.email,
            password=request.password,
            role=request.role,
            age=request.age,
            sex=request.sex,
            contact_number=request.contact_number,
            emergency_number=request.emergency_number,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = create_access_token(user["id"])
    return AuthResponse(access_token=token, user=CurrentUser.model_validate(user))


@router.post("/auth/login", response_model=AuthResponse)
def login(request: LoginRequest):
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user["id"])
    return AuthResponse(access_token=token, user=CurrentUser.model_validate(user))


@router.get("/auth/me", response_model=CurrentUser)
def me(current_user: CurrentUser = Depends(get_current_user)):
    return current_user


@router.put("/auth/me", response_model=CurrentUser)
def update_me(request: UpdateProfileRequest, current_user: CurrentUser = Depends(get_current_user)):
    try:
        updated_user = upsert_patient_profile(
            current_user.id,
            name=request.name,
            email=request.email,
            age=request.age,
            sex=request.sex,
            contact_number=request.contact_number,
            emergency_number=request.emergency_number,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return CurrentUser.model_validate(updated_user)


@router.get("/patient_history", response_model=PatientHistoryResponse)
def patient_history(current_user: CurrentUser = Depends(get_current_user)):
    history = get_patient_history(current_user.id)
    return PatientHistoryResponse(items=history)


@router.get("/patient_history/{patient_id}", response_model=PatientHistoryResponse)
def patient_history_for_doctor(patient_id: UUID, current_user: CurrentUser = Depends(get_current_user)):
    ensure_doctor_access(current_user)
    history = get_patient_history(patient_id)
    return PatientHistoryResponse(items=history)