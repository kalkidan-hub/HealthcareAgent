from fastapi import APIRouter, Depends, HTTPException, status

from backend.infrastructure.auth import get_current_user
from backend.infrastructure.db_repo import authenticate_user, create_access_token, create_user_account
from backend.models.auth import AuthResponse, CurrentUser, LoginRequest, RegisterRequest


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