from typing import Annotated

from fastapi import Depends

from app.api.dependencies.users import get_user_service
from app.services.user_service import UserService

UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]