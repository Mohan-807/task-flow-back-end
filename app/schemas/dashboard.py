from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.project import TaskCounts
from app.schemas.user import UserSummary


class DashboardStatsResponse(BaseModel):
    activeProjects: int
    totalTasks: int
    teamMembers: int
    completionRate: int


class MemberAvatar(BaseModel):
    id: int
    initials: str | None
    color: str | None
    avatarUrl: str | None


class RecentProjectResponse(BaseModel):
    id: int
    name: str
    status: str
    priority: str
    color: str
    progress: int
    dueDate: date | None
    tasksCount: TaskCounts
    members: list[MemberAvatar]
    updatedAt: datetime


class RecentTaskResponse(BaseModel):
    id: int
    title: str
    projectId: int
    projectName: str
    status: str
    priority: str
    dueDate: date | None
    commentsCount: int
    assigneeId: int | None
    assignee: UserSummary | None
    updatedAt: datetime
