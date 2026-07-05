from fastapi import APIRouter

from app.api.dependencies.types import UserServiceDep
from app.schemas.user import UserCreate, UserResponse, UserUpdate


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse,
                 status_code=201,
                 summary="Create a new user",
                 description="Creates a new user in the system.",
            )

def create_user(
    user: UserCreate,
    user_service: UserServiceDep,
):
    return user_service.create_user(user)

@router.get("", response_model=list[UserResponse])
def get_users(
    user_service: UserServiceDep,
):
    return user_service.get_users()

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    user_service: UserServiceDep,
):
    return user_service.get_user_by_id(user_id)

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserUpdate,
    user_service: UserServiceDep,
):
    return user_service.update_user(user_id, user)

@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    user_id: int,
    user_service: UserServiceDep,
):
    return user_service.delete_user(user_id)