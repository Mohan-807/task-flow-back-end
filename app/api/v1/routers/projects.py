from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import require_roles
from app.api.dependencies.types import CurrentUserDep, ProjectServiceDep
from app.models.user import User
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
    _caller: Annotated[User, Depends(require_roles("admin", "manager"))],
    project_service: ProjectServiceDep,
):
    return project_service.update_project(project_id, project)

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
    _caller: Annotated[User, Depends(require_roles("admin", "manager"))],
    project_service: ProjectServiceDep,
):
    return project_service.add_member(project_id, request)

@router.delete(
    "/{project_id}/members/{user_id}",
    response_model=DataListResponse[ProjectMemberResponse],
)
def remove_project_member(
    project_id: int,
    user_id: int,
    _caller: Annotated[User, Depends(require_roles("admin", "manager"))],
    project_service: ProjectServiceDep,
):
    return project_service.remove_member(project_id, user_id)

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
