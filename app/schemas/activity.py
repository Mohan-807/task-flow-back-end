from datetime import datetime

from pydantic import BaseModel

from app.schemas.user import UserSummary


class ActivityResponse(BaseModel):
    id: int
    type: str
    userId: int
    user: UserSummary
    projectId: int | None
    taskId: int | None
    message: str
    createdAt: datetime
