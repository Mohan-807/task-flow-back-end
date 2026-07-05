from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import require_roles
from app.api.dependencies.types import CurrentUserDep, UserServiceDep
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.user import (
    InviteUserRequest,
    InviteUserResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)


router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    summary="Create a new user",
    description="Creates a new user in the system.",
)
def create_user(
    user: UserCreate,
    user_service: UserServiceDep,
    _admin: Annotated[User, Depends(require_roles("admin"))],
):
    return user_service.create_user(user)

@router.post("/invite", response_model=InviteUserResponse, status_code=201)
def invite_user(
    invite: InviteUserRequest,
    user_service: UserServiceDep,
    _caller: Annotated[User, Depends(require_roles("admin", "manager"))],
):
    return user_service.invite_user(invite)

@router.get("", response_model=PaginatedResponse[UserResponse])
def get_users(
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
    search: str | None = None,
    role: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=100),
):
    return user_service.list_users(
        search=search,
        role=role,
        status=status,
        page=page,
        per_page=per_page,
    )

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
):
    return user_service.get_user_by_id(user_id)

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserUpdate,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
):
    return user_service.update_user(user_id, user, current_user)

@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    user_service: UserServiceDep,
):
    user_service.delete_user(user_id, current_user)