from jose import JWTError

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.exceptions import InactiveAccountException, UnauthorizedException
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserResponse

# Hashed once at import time so a login attempt for a non-existent email still
# runs a real bcrypt comparison, taking roughly the same time as a real user
# with a wrong password. Without this, "no such user" would return near-instantly
# while "wrong password" takes ~100ms, letting an attacker enumerate registered
# emails purely from response timing.
_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing-safety")

_INVALID_REFRESH_TOKEN = "Invalid or expired refresh token"


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
            user=UserResponse.model_validate(user),
        )

    def get_current_user_profile(self, current_user: User) -> UserResponse:
        user = self.user_repository.touch_last_active(current_user)
        return UserResponse.model_validate(user)

    def refresh(self, refresh_token: str) -> LoginResponse:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise UnauthorizedException(_INVALID_REFRESH_TOKEN)

        if payload.get("type") != "refresh":
            raise UnauthorizedException(_INVALID_REFRESH_TOKEN)

        user = self.user_repository.get_by_id(int(payload["sub"]))
        if user is None or user.status == "inactive":
            raise UnauthorizedException(_INVALID_REFRESH_TOKEN)

        new_access_token = create_access_token(user_id=user.id, role=user.role)
        new_refresh_token = create_refresh_token(user_id=user.id)

        return LoginResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )
