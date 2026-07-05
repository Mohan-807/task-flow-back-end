from app.api.dependencies.users import UserRepositoryDep
from app.services.auth_service import AuthService


def get_auth_service(
    user_repository: UserRepositoryDep,
) -> AuthService:
    return AuthService(
        user_repository=user_repository,
    )