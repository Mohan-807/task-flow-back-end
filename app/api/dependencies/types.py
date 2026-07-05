from typing import Annotated

from fastapi import Depends

from app.api.dependencies.activity_service import get_activity_service
from app.api.dependencies.auth import get_auth_service, get_current_user
from app.api.dependencies.comments import get_comment_service
from app.api.dependencies.dashboard import get_dashboard_service
from app.api.dependencies.projects import get_project_service
from app.api.dependencies.settings import get_settings_service
from app.api.dependencies.tasks import get_task_service
from app.api.dependencies.users import get_user_service
from app.models.user import User
from app.services.user_service import UserService
from app.services.activity_service import ActivityService
from app.services.auth_service import AuthService
from app.services.comment_service import CommentService
from app.services.dashboard_service import DashboardService
from app.services.project_service import ProjectService
from app.services.settings_service import SettingsService
from app.services.task_service import TaskService

UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]

AuthServiceDep = Annotated[
    AuthService,
    Depends(get_auth_service),
]

ProjectServiceDep = Annotated[
    ProjectService,
    Depends(get_project_service),
]

TaskServiceDep = Annotated[
    TaskService,
    Depends(get_task_service),
]

CommentServiceDep = Annotated[
    CommentService,
    Depends(get_comment_service),
]

ActivityServiceDep = Annotated[
    ActivityService,
    Depends(get_activity_service),
]

DashboardServiceDep = Annotated[
    DashboardService,
    Depends(get_dashboard_service),
]

SettingsServiceDep = Annotated[
    SettingsService,
    Depends(get_settings_service),
]

CurrentUserDep = Annotated[
    User,
    Depends(get_current_user),
]