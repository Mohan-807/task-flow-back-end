from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["admin", "manager", "developer", "tester"]
UserStatus = Literal["active", "inactive", "invited"]
InvitableRole = Literal["manager", "developer", "tester"]


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)
    role: Role
    status: UserStatus = "active"
    department: str | None = Field(default=None, max_length=100)
    color: str | None = None


class UserResponse(BaseModel):
    # populate_by_name lets this validate from an ORM object's snake_case
    # attrs (via validation_alias) AND from plain camelCase kwargs in Python
    # (e.g. rebuilding one UserResponse's data into a subclass like
    # InviteUserResponse) — without it, only the alias form works.
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    email: EmailStr
    role: str
    avatarUrl: str | None = Field(validation_alias="avatar_url")
    initials: str | None
    color: str | None
    status: str
    department: str | None
    joinedAt: datetime = Field(validation_alias="joined_at")
    lastActiveAt: datetime | None = Field(validation_alias="last_active_at")


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    role: Role | None = None
    status: UserStatus | None = None
    department: str | None = Field(default=None, max_length=100)
    color: str | None = None


class InviteUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    role: InvitableRole


class InviteUserResponse(UserResponse):
    # No email-sending service exists yet, so the temp password is returned
    # directly here instead of being emailed — revisit once real delivery
    # exists, and consider forcing a password change on first login then.
    temporaryPassword: str