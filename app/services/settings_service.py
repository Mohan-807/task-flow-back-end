from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.settings import (
    AppearancePreferencesRequest,
    AppearancePreferencesResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    NotificationPreferencesRequest,
    NotificationPreferencesResponse,
    ProfileUpdateRequest,
)
from app.schemas.user import UserResponse, UserUpdate
from app.core.constants import DEFAULT_APPEARANCE_PREFERENCES, DEFAULT_NOTIFICATION_PREFERENCES
from app.core.exceptions import IncorrectPasswordException, PasswordMismatchException
from app.core.security import hash_password, verify_password
from app.services.user_service import UserService


class SettingsService:
    def __init__(
        self,
        user_repository: UserRepository,
        user_service: UserService,
    ):
        self.user_repository = user_repository
        self.user_service = user_service

    def update_profile(
        self,
        current_user: User,
        request: ProfileUpdateRequest,
    ) -> UserResponse:
        # Deliberately the exact same code path as PATCH /users/{user_id> for
        # a user editing themselves — the spec's own note says these may
        # share a handler, and update_user already enforces "self editing
        # only touches name/email/department/color", which is all this
        # schema exposes anyway.
        update = UserUpdate(**request.model_dump(exclude_unset=True))
        return self.user_service.update_user(current_user.id, update, current_user)

    def change_password(
        self,
        current_user: User,
        request: ChangePasswordRequest,
    ) -> ChangePasswordResponse:
        if not verify_password(request.currentPassword, current_user.hashed_password):
            raise IncorrectPasswordException()

        if request.newPassword != request.confirmPassword:
            raise PasswordMismatchException()

        self.user_repository.update(
            current_user.id, {"hashed_password": hash_password(request.newPassword)}
        )

        # Spec asks to "invalidate all existing refresh tokens for this user"
        # here — moot: this project deliberately has no server-side refresh
        # token storage/revocation (see project memory / auth phase notes),
        # so there is nothing to invalidate.
        return ChangePasswordResponse(message="Password changed successfully")

    def update_notification_preferences(
        self,
        current_user: User,
        request: NotificationPreferencesRequest,
    ) -> NotificationPreferencesResponse:
        current = current_user.notification_preferences or dict(
            DEFAULT_NOTIFICATION_PREFERENCES
        )
        merged = {**current, **request.model_dump(exclude_unset=True)}

        updated_user = self.user_repository.update(
            current_user.id, {"notification_preferences": merged}
        )

        return NotificationPreferencesResponse(**updated_user.notification_preferences)

    def update_appearance_preferences(
        self,
        current_user: User,
        request: AppearancePreferencesRequest,
    ) -> AppearancePreferencesResponse:
        current = current_user.appearance_preferences or dict(
            DEFAULT_APPEARANCE_PREFERENCES
        )
        merged = {**current, **request.model_dump(exclude_unset=True)}

        updated_user = self.user_repository.update(
            current_user.id, {"appearance_preferences": merged}
        )

        return AppearancePreferencesResponse(**updated_user.appearance_preferences)
