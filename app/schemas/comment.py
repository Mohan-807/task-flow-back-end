from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserSummary


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    id: int
    taskId: int
    userId: int
    author: UserSummary
    content: str
    isEdited: bool
    createdAt: datetime
    updatedAt: datetime


class CommentUpdateResponse(BaseModel):
    id: int
    taskId: int
    userId: int
    content: str
    isEdited: bool
    createdAt: datetime
    updatedAt: datetime
