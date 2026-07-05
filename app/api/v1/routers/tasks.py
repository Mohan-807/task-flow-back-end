from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.auth import require_roles
from app.api.dependencies.types import (
    ActivityServiceDep,
    CommentServiceDep,
    CurrentUserDep,
    TaskServiceDep,
)
from app.models.user import User
from app.schemas.activity import ActivityResponse
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.common import DataListResponse, PaginatedResponse
from app.schemas.kanban import MoveTaskRequest, MoveTaskResponse
from app.schemas.task import (
    TaskAssigneeUpdateRequest,
    TaskAssigneeUpdateResponse,
    TaskDetailResponse,
    TaskDueDateUpdateRequest,
    TaskDueDateUpdateResponse,
    TaskPriorityUpdateRequest,
    TaskPriorityUpdateResponse,
    TaskStatusUpdateRequest,
    TaskStatusUpdateResponse,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(
    task_id: int,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
):
    return task_service.get_task_by_id(task_id, current_user)

@router.patch("/{task_id}", response_model=TaskDetailResponse)
def update_task(
    task_id: int,
    task: TaskUpdate,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
):
    return task_service.update_task(task_id, task, current_user)

@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
):
    task_service.delete_task(task_id, current_user)

@router.patch("/{task_id}/status", response_model=TaskStatusUpdateResponse)
def update_task_status(
    task_id: int,
    request: TaskStatusUpdateRequest,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
):
    return task_service.update_task_status(task_id, request, current_user)

@router.patch("/{task_id}/priority", response_model=TaskPriorityUpdateResponse)
def update_task_priority(
    task_id: int,
    request: TaskPriorityUpdateRequest,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
):
    return task_service.update_task_priority(task_id, request, current_user)

@router.patch("/{task_id}/assignee", response_model=TaskAssigneeUpdateResponse)
def update_task_assignee(
    task_id: int,
    request: TaskAssigneeUpdateRequest,
    current_user: Annotated[User, Depends(require_roles("admin", "manager"))],
    task_service: TaskServiceDep,
):
    return task_service.update_task_assignee(task_id, request, current_user)

@router.patch("/{task_id}/due-date", response_model=TaskDueDateUpdateResponse)
def update_task_due_date(
    task_id: int,
    request: TaskDueDateUpdateRequest,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
):
    return task_service.update_task_due_date(task_id, request, current_user)

@router.patch("/{task_id}/move", response_model=MoveTaskResponse)
def move_task(
    task_id: int,
    request: MoveTaskRequest,
    current_user: CurrentUserDep,
    task_service: TaskServiceDep,
):
    return task_service.move_task(task_id, request, current_user)

@router.get("/{task_id}/comments", response_model=PaginatedResponse[CommentResponse])
def get_task_comments(
    task_id: int,
    current_user: CurrentUserDep,
    comment_service: CommentServiceDep,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1),
):
    return comment_service.list_comments(task_id, current_user, page, per_page)

@router.post("/{task_id}/comments", response_model=CommentResponse, status_code=201)
def add_task_comment(
    task_id: int,
    comment: CommentCreate,
    current_user: CurrentUserDep,
    comment_service: CommentServiceDep,
):
    return comment_service.add_comment(task_id, comment, current_user)

@router.get("/{task_id}/activities", response_model=DataListResponse[ActivityResponse])
def get_task_activities(
    task_id: int,
    current_user: CurrentUserDep,
    activity_service: ActivityServiceDep,
    limit: int = Query(default=5, ge=1, le=50),
):
    return activity_service.list_task_activities(task_id, current_user, limit)
