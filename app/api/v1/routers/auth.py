from fastapi import APIRouter

from app.api.dependencies.types import AuthServiceDep, CurrentUserDep
from app.schemas.auth import (
    AuthUserResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=LoginResponse)
def login(
    login_request: LoginRequest,
    auth_service: AuthServiceDep,
):
    return auth_service.login(login_request)


@router.get("/me", response_model=AuthUserResponse)
def get_me(
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
):
    return auth_service.get_current_user_profile(current_user)


@router.post("/token/refresh", response_model=LoginResponse)
def refresh_token(
    refresh_request: RefreshTokenRequest,
    auth_service: AuthServiceDep,
):
    return auth_service.refresh(refresh_request.refresh_token)
