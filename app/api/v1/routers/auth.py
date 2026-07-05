from fastapi import APIRouter

from app.api.dependencies.types import AuthServiceDep
from app.schemas.auth import LoginRequest, LoginResponse

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