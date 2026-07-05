from typing import Annotated

from fastapi import Depends

from app.api.dependencies.auth import get_auth_service, get_current_user
from app.api.dependencies.users import get_user_service
from app.models.user import User
from app.services.user_service import UserService
from app.services.auth_service import AuthService

UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]

AuthServiceDep = Annotated[
    AuthService,
    Depends(get_auth_service),
]

CurrentUserDep = Annotated[
    User,
    Depends(get_current_user),
]