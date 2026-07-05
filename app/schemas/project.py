from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user import Role

ProjectStatus = Literal["active", "completed"]
Priority = Literal["critical", "high", "medium", "low"]


def _validate_tags(tags: list[str]) -> list[str]:
    for tag in tags:
        if len(tag) > 30:
            raise ValueError("each tag must be at most 30 characters")
    return tags


class TaskCounts(BaseModel):
    total: int
    todo: int
    inProgress: int
    testing: int
    done: int


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    description: str | None = Field(default=None, max_length=500)
    priority: Priority
    status: ProjectStatus = "active"
    color: str = "#6366f1"
    dueDate: date | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("dueDate")
    @classmethod
    def due_date_must_be_future(cls, value: date | None) -> date | None:
        if value is not None and value <= date.today():
            raise ValueError("dueDate must be in the future")
        return value

    @field_validator("tags")
    @classmethod
    def tags_length(cls, value: list[str]) -> list[str]:
        return _validate_tags(value)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    description: str | None = Field(default=None, max_length=500)
    status: ProjectStatus | None = None
    priority: Priority | None = None
    color: str | None = None
    dueDate: date | None = None
    tags: list[str] | None = None

    @field_validator("dueDate")
    @classmethod
    def due_date_must_be_future(cls, value: date | None) -> date | None:
        if value is not None and value <= date.today():
            raise ValueError("dueDate must be in the future")
        return value

    @field_validator("tags")
    @classmethod
    def tags_length(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return _validate_tags(value)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    description: str | None
    status: str
    priority: str
    color: str
    progress: int
    startDate: date = Field(validation_alias="start_date")
    dueDate: date | None = Field(validation_alias="due_date")
    ownerId: int = Field(validation_alias="owner_id")
    memberIds: list[int]
    tags: list[str]
    tasksCount: TaskCounts
    createdAt: datetime = Field(validation_alias="created_at")
    updatedAt: datetime = Field(validation_alias="updated_at")


class ProjectMemberResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    avatarUrl: str | None
    initials: str | None
    color: str | None
    status: str
    department: str | None
    isOwner: bool


class AddMemberRequest(BaseModel):
    user_id: int


class UpdateMemberRoleRequest(BaseModel):
    role: Role


class UpdateMemberRoleResponse(BaseModel):
    id: int
    name: str
    role: str
    updatedAt: datetime
