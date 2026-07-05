from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.constants import USER_COLOR_PALETTE

Theme = Literal["light", "dark", "system"]
Density = Literal["compact", "default", "comfortable"]


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    department: str | None = Field(default=None, max_length=100)
    color: str | None = None

    @field_validator("color")
    @classmethod
    def color_in_palette(cls, value: str | None) -> str | None:
        if value is not None and value not in USER_COLOR_PALETTE:
            raise ValueError(f"color must be one of {', '.join(USER_COLOR_PALETTE)}")
        return value


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str = Field(min_length=6)
    confirmPassword: str


class ChangePasswordResponse(BaseModel):
    message: str


class NotificationPreferencesRequest(BaseModel):
    taskAssigned: bool | None = None
    taskCompleted: bool | None = None
    commentAdded: bool | None = None
    projectCreated: bool | None = None
    memberAdded: bool | None = None
    weeklyDigest: bool | None = None


class NotificationPreferencesResponse(BaseModel):
    taskAssigned: bool
    taskCompleted: bool
    commentAdded: bool
    projectCreated: bool
    memberAdded: bool
    weeklyDigest: bool


class AppearancePreferencesRequest(BaseModel):
    theme: Theme | None = None
    density: Density | None = None


class AppearancePreferencesResponse(BaseModel):
    theme: str
    density: str
