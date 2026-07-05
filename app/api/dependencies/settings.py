from fastapi import Depends

from app.api.dependencies.users import UserRepositoryDep, get_user_service
from app.services.settings_service import SettingsService
from app.services.user_service import UserService


def get_settings_service(
    user_repository: UserRepositoryDep,
    user_service: UserService = Depends(get_user_service),
) -> SettingsService:
    return SettingsService(user_repository, user_service)
