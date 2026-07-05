from app.repositories.user_repository import UserRepository
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.core.exceptions import InactiveAccountException, UnauthorizedException
from app.schemas.auth import AuthUserResponse, LoginRequest, LoginResponse

# Hashed once at import time so a login attempt for a non-existent email still
# runs a real bcrypt comparison, taking roughly the same time as a real user
# with a wrong password. Without this, "no such user" would return near-instantly
# while "wrong password" takes ~100ms, letting an attacker enumerate registered
# emails purely from response timing.
_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing-safety")


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
    ):
        self.user_repository = user_repository

    def login(
        self,
        login_request: LoginRequest,
    ) -> LoginResponse:
        user = self.user_repository.get_by_email(login_request.email)

        password_hash = user.hashed_password if user else _DUMMY_PASSWORD_HASH
        password_is_valid = verify_password(login_request.password, password_hash)

        if not user or not password_is_valid:
            raise UnauthorizedException("Invalid email or password")

        if user.status == "inactive":
            raise InactiveAccountException()

        user = self.user_repository.touch_last_active(user)

        access_token = create_access_token(user_id=user.id, role=user.role)
        refresh_token = create_refresh_token(user_id=user.id)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=AuthUserResponse.model_validate(user),
        )