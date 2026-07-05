from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.api.dependencies.users import UserRepositoryDep
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.models.user import User
from app.services.auth_service import AuthService

# auto_error=False so a missing header doesn't short-circuit into FastAPI's
# default 403 — the spec requires 401 "Not authenticated" for that case, so we
# check for None ourselves below and raise it explicitly.
bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(
    user_repository: UserRepositoryDep,
) -> AuthService:
    return AuthService(
        user_repository=user_repository,
    )


def get_current_user(
    user_repository: UserRepositoryDep,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise UnauthorizedException("Not authenticated")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise UnauthorizedException("Not authenticated")

    if payload.get("type") != "access":
        raise UnauthorizedException("Not authenticated")

    user = user_repository.get_by_id(int(payload["sub"]))
    if user is None:
        raise UnauthorizedException("Not authenticated")

    return user