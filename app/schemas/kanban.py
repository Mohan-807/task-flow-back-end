from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.task import TaskStatus
from app.schemas.user import UserSummary


class KanbanTask(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    assigneeId: int | None
    assignee: UserSummary | None
    reporterId: int
    dueDate: date | None
    tags: list[str]
    commentsCount: int
    columnOrder: int


class KanbanColumn(BaseModel):
    label: str
    tasks: list[KanbanTask]


class KanbanBoardResponse(BaseModel):
    projectId: int
    columns: dict[str, KanbanColumn]


class MoveTaskRequest(BaseModel):
    status: TaskStatus
    columnOrder: int = Field(ge=0)


class MoveTaskResponse(BaseModel):
    id: int
    status: str
    columnOrder: int
    updatedAt: datetime


class ColumnStat(BaseModel):
    count: int
    percentage: int


class KanbanStatsResponse(BaseModel):
    projectId: int
    total: int
    todo: ColumnStat
    in_progress: ColumnStat
    testing: ColumnStat
    done: ColumnStat
    progress: int
