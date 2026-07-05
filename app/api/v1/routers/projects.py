from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import require_roles
from app.api.dependencies.types import (
    ActivityServiceDep,
    CurrentUserDep,
    ProjectServiceDep,
    TaskServiceDep,
)
from app.models.user import User
from app.schemas.activity import ActivityResponse
from app.schemas.common import DataListResponse, PaginatedResponse
from app.schemas.project import (
    AddMemberRequest,
    ProjectCreate,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
    UpdateMemberRoleRequest,
    UpdateMemberRoleResponse,
)
from app.schemas.kanban import KanbanBoardResponse, KanbanStatsResponse
from app.schemas.task import TaskCreate, TaskResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    project: ProjectCreate,
    current_user: Annotated[User, Depends(require_roles("admin", "manager"))],
    project_service: ProjectServiceDep,
):
    return project_service.create_project(project, current_user)

@router.get("", response_model=PaginatedResponse[ProjectResponse])
def get_projects(
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
    status: str | None = None,
    search: str | None = None,
    priority: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
):
    return project_service.list_projects(
        current_user=current_user,
        status=status,
        search=search,
        priority=priority,
        page=page,
        per_page=per_page,
    )

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
):
    return project_service.get_project_by_id(project_id, current_user)

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project: ProjectUpdate,
    current_user: Annotated[User, Depends(require_roles("admin", "manager"))],
    project_service: ProjectServiceDep,
):
    return project_service.update_project(project_id, project, current_user)

@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    _caller: Annotated[User, Depends(require_roles("admin", "manager"))],
    project_service: ProjectServiceDep,
):
    project_service.delete_project(project_id)

@router.get("/{project_id}/members", response_model=DataListResponse[ProjectMemberResponse])
def get_project_members(
    project_id: int,
    current_user: CurrentUserDep,
    project_service: ProjectServiceDep,
):
    return project_service.list_members(project_id, current_user)

@router.post("/{project_id}/members", response_model=DataListResponse[ProjectMemberResponse])
def add_project_member(
    project_id: int,
    request: AddMemberRequest,
    current_user: Annotated[User, Depends(require_roles("admin", "manager"))],
    project_service: ProjectServiceDep,
):
    return project_service.add_member(project_id, request, current_user)

@router.delete(
    "/{project_id}/members/{user_id}",
    response_model=DataListResponse[ProjectMemberResponse],
)
def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: Annotated[User, Depends(require_roles("admin", "manager"))],
    project_service: ProjectServiceDep,
):
    return project_service.remove_member(project_id, user_id, current_user)

@router.patch(
    "/{project_id}/members/{user_id}",
    response_model=UpdateMemberRoleResponse,
)
def update_project_member_role(
    project_id: int,
    user_id: int,
    request: UpdateMemberRoleRequest,
    current_user: Annotated[User, Depends(require_roles("admin", "manager"))],
    project_service: ProjectServiceDep,
):
    return project_service.update_member_role(project_id, user_id, request, current_user)

@router.get("/{project_id}/tasks", response_model=PaginatedResponse[TaskResponse])
def get_project_tasks(
    project_id: int,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
    status: str | None = None,
    priority: str | None = None,
    assignee_id: int | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, ge=1, le=200),
):
    return task_service.list_tasks(
        project_id=project_id,
        current_user=current_user,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        page=page,
        per_page=per_page,
    )

@router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=201)
def create_project_task(
    project_id: int,
    task: TaskCreate,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
):
    return task_service.create_task(project_id, task, current_user)

@router.get("/{project_id}/kanban", response_model=KanbanBoardResponse)
def get_kanban_board(
    project_id: int,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
):
    return task_service.get_kanban_board(project_id, current_user)

@router.get("/{project_id}/kanban/stats", response_model=KanbanStatsResponse)
def get_kanban_stats(
    project_id: int,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
):
    return task_service.get_kanban_stats(project_id, current_user)

@router.get("/{project_id}/activities", response_model=PaginatedResponse[ActivityResponse])
def get_project_activities(
    project_id: int,
    current_user: CurrentUserDep,
    activity_service: ActivityServiceDep,
    limit: int | None = Query(default=None, ge=1, le=50),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1),
):
    return activity_service.list_project_activities(
        project_id, current_user, limit, page, per_page
    )
