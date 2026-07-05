import math
import random

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.user import (
    InviteUserRequest,
    InviteUserResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.core.constants import USER_COLOR_PALETTE
from app.core.exceptions import (
    CannotDeleteSelfException,
    EmailAlreadyExistsException,
    InsufficientPermissionsException,
    UserNotFoundException,
)
from app.core.security import generate_temporary_password, hash_password
from app.core.utils import generate_initials

_ADMIN_ONLY_FIELDS = {"role", "status"}


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, user_data: UserCreate) -> UserResponse:
        if self.user_repository.get_by_email(user_data.email):
            raise EmailAlreadyExistsException()

        user = self.user_repository.create(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
            status=user_data.status,
            department=user_data.department,
            color=user_data.color or random.choice(USER_COLOR_PALETTE),
            initials=generate_initials(user_data.name),
        )

        return UserResponse.model_validate(user)

    def list_users(
        self,
        search: str | None,
        role: str | None,
        status: str | None,
        page: int,
        per_page: int,
    ) -> PaginatedResponse[UserResponse]:
        users, total = self.user_repository.get_filtered(
            search=search,
            role=role,
            status=status,
            page=page,
            per_page=per_page,
        )

        return PaginatedResponse(
            data=[UserResponse.model_validate(user) for user in users],
            pagination=PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=math.ceil(total / per_page),
            ),
        )

    def get_user_by_id(self, user_id: int) -> UserResponse:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()
        return UserResponse.model_validate(user)

    def update_user(
        self,
        user_id: int,
        user_update: UserUpdate,
        current_user: User,
    ) -> UserResponse:
        is_admin = current_user.role == "admin"
        is_self = current_user.id == user_id

        # Checked before touching the DB: a non-admin poking at someone else's
        # id gets a flat 403 without us revealing whether that id even exists.
        if not is_admin and not is_self:
            raise InsufficientPermissionsException()

        target_user = self.user_repository.get_by_id(user_id)
        if not target_user:
            raise UserNotFoundException()

        update_fields = user_update.model_dump(exclude_unset=True)

        if not is_admin and _ADMIN_ONLY_FIELDS & update_fields.keys():
            raise InsufficientPermissionsException()

        if "email" in update_fields and update_fields["email"] != target_user.email:
            if self.user_repository.get_by_email(update_fields["email"]):
                raise EmailAlreadyExistsException()

        if "name" in update_fields:
            update_fields["initials"] = generate_initials(update_fields["name"])

        updated_user = self.user_repository.update(user_id, update_fields)
        return UserResponse.model_validate(updated_user)

    def delete_user(self, user_id: int, current_user: User) -> None:
        if current_user.id == user_id:
            raise CannotDeleteSelfException()

        user = self.user_repository.delete(user_id)
        if not user:
            raise UserNotFoundException()

    def invite_user(self, invite_data: InviteUserRequest) -> InviteUserResponse:
        if self.user_repository.get_by_email(invite_data.email):
            raise EmailAlreadyExistsException()

        temporary_password = generate_temporary_password()

        user = self.user_repository.create(
            name=invite_data.name,
            email=invite_data.email,
            hashed_password=hash_password(temporary_password),
            role=invite_data.role,
            status="invited",
            department=None,
            color=random.choice(USER_COLOR_PALETTE),
            initials=generate_initials(invite_data.name),
        )

        return InviteUserResponse(
            **UserResponse.model_validate(user).model_dump(),
            temporaryPassword=temporary_password,
        )