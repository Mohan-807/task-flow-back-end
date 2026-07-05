from app.repositories.user_repository import UserRepository
from app.core.security import verify_password
from app.core.exceptions import UnauthorizedException
from app.schemas.auth import LoginRequest


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
    ):
        self.user_repository = user_repository

    def login(
    self,
    login_request: LoginRequest,
    ):
        user = self.user_repository.get_by_email(
            login_request.email
        )

        if not user:
            raise UnauthorizedException(
                "Invalid email or password"
            )

        if not verify_password(
            login_request.password,
            user.password,
        ):
            raise UnauthorizedException(
                "Invalid email or password"
            )

        return user