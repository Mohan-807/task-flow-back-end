from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.project import Priority
from app.schemas.user import UserSummary

TaskStatus = Literal["todo", "in_progress", "testing", "done"]


def _validate_tags(tags: list[str]) -> list[str]:
    for tag in tags:
        if len(tag) > 30:
            raise ValueError("each tag must be at most 30 characters")
    return tags


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus = "todo"
    priority: Priority = "medium"
    assigneeId: int | None = None
    dueDate: date | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def tags_length(cls, value: list[str]) -> list[str]:
        return _validate_tags(value)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = None

    @field_validator("tags")
    @classmethod
    def tags_length(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return _validate_tags(value)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    title: str
    description: str | None
    status: str
    priority: str
    projectId: int = Field(validation_alias="project_id")
    assigneeId: int | None = Field(validation_alias="assignee_id")
    reporterId: int = Field(validation_alias="reporter_id")
    dueDate: date | None = Field(validation_alias="due_date")
    tags: list[str]
    commentsCount: int
    columnOrder: int = Field(validation_alias="column_order")
    createdAt: datetime = Field(validation_alias="created_at")
    updatedAt: datetime = Field(validation_alias="updated_at")


class TaskDetailResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    priority: str
    projectId: int
    projectName: str
    assigneeId: int | None
    assignee: UserSummary | None
    reporterId: int
    reporter: UserSummary
    dueDate: date | None
    tags: list[str]
    commentsCount: int
    columnOrder: int
    createdAt: datetime
    updatedAt: datetime


class TaskStatusUpdateRequest(BaseModel):
    status: TaskStatus


class TaskStatusUpdateResponse(BaseModel):
    id: int
    status: str
    updatedAt: datetime


class TaskPriorityUpdateRequest(BaseModel):
    priority: Priority


class TaskPriorityUpdateResponse(BaseModel):
    id: int
    priority: str
    updatedAt: datetime


class TaskAssigneeUpdateRequest(BaseModel):
    assigneeId: int | None


class TaskAssigneeUpdateResponse(BaseModel):
    id: int
    assigneeId: int | None
    assignee: UserSummary | None
    updatedAt: datetime


class TaskDueDateUpdateRequest(BaseModel):
    dueDate: date | None


class TaskDueDateUpdateResponse(BaseModel):
    id: int
    dueDate: date | None
    updatedAt: datetime
