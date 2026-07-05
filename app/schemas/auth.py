from pydantic import BaseModel, EmailStr,ConfigDict, Field
from datetime import datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    avatarUrl: str | None = Field(validation_alias="avatar_url")
    initials: str
    color: str
    status: str
    department: str | None
    joinedAt: datetime = Field(validation_alias="joined_at")
    lastActiveAt: datetime | None = Field(validation_alias="last_active_at")


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: AuthUserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str