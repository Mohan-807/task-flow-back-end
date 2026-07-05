from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import require_roles
from app.api.dependencies.types import ActivityServiceDep
from app.models.user import User
from app.schemas.activity import ActivityResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/activities", tags=["Activities"])


@router.get("", response_model=PaginatedResponse[ActivityResponse])
def get_global_activities(
    _caller: Annotated[User, Depends(require_roles("admin", "manager"))],
    activity_service: ActivityServiceDep,
    type: str | None = None,
    user_id: int | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
):
    return activity_service.list_global_activities(
        type=type, user_id=user_id, page=page, per_page=per_page
    )
