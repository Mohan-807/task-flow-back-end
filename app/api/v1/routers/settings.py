from fastapi import APIRouter

from app.api.dependencies.types import CurrentUserDep, SettingsServiceDep
from app.schemas.settings import (
    AppearancePreferencesRequest,
    AppearancePreferencesResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    NotificationPreferencesRequest,
    NotificationPreferencesResponse,
    ProfileUpdateRequest,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.patch("/profile", response_model=UserResponse)
def update_profile(
    request: ProfileUpdateRequest,
    current_user: CurrentUserDep,
    settings_service: SettingsServiceDep,
):
    return settings_service.update_profile(current_user, request)

@router.patch("/password", response_model=ChangePasswordResponse)
def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUserDep,
    settings_service: SettingsServiceDep,
):
    return settings_service.change_password(current_user, request)

@router.patch("/notifications", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    request: NotificationPreferencesRequest,
    current_user: CurrentUserDep,
    settings_service: SettingsServiceDep,
):
    return settings_service.update_notification_preferences(current_user, request)

@router.patch("/appearance", response_model=AppearancePreferencesResponse)
def update_appearance_preferences(
    request: AppearancePreferencesRequest,
    current_user: CurrentUserDep,
    settings_service: SettingsServiceDep,
):
    return settings_service.update_appearance_preferences(current_user, request)
