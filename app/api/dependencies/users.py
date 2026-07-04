from fastapi import Depends
from app.api.dependencies.db import DBSession

from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


def get_user_repository(
    db: DBSession,
) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repository)