import math

from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.task import (
    TaskAssigneeUpdateRequest,
    TaskAssigneeUpdateResponse,
    TaskCreate,
    TaskDetailResponse,
    TaskDueDateUpdateRequest,
    TaskDueDateUpdateResponse,
    TaskPriorityUpdateRequest,
    TaskPriorityUpdateResponse,
    TaskResponse,
    TaskStatusUpdateRequest,
    TaskStatusUpdateResponse,
    TaskUpdate,
)
from app.schemas.kanban import (
    ColumnStat,
    KanbanBoardResponse,
    KanbanColumn,
    KanbanStatsResponse,
    KanbanTask,
    MoveTaskRequest,
    MoveTaskResponse,
)
from app.schemas.user import UserSummary
from app.core.activity_templates import (
    PRIORITY_LABELS,
    STATUS_LABELS,
    render_activity_message,
)
from app.core.exceptions import (
    AssigneeNotProjectMemberException,
    CannotMoveTaskException,
    CannotReopenCompletedTaskException,
    CannotReopenTaskViaMoveException,
    ProjectNotFoundException,
    TaskDeletePermissionException,
    TaskEditPermissionException,
    TaskNotFoundException,
)
from app.repositories.activity_repository import ActivityRepository
from app.services.access_control import check_project_access, check_task_access
from app.services.task_stats import TASK_STATUSES, count_by_status

_COLUMN_LABELS = {
    "todo": "To Do",
    "in_progress": "In Progress",
    "testing": "Testing",
    "done": "Done",
}

# Roles that can act on any task in a project they have access to; a developer
# is restricted to tasks where they're personally involved (assignee/reporter).
_TASK_EDIT_ROLES = {"admin", "manager", "tester"}


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        project_repository: ProjectRepository,
        activity_repository: ActivityRepository,
    ):
        self.task_repository = task_repository
        self.project_repository = project_repository
        self.activity_repository = activity_repository

    def list_tasks(
        self,
        project_id: int,
        current_user: User,
        status: str | None,
        priority: str | None,
        assignee_id: int | None,
        search: str | None,
        page: int,
        per_page: int,
    ) -> PaginatedResponse[TaskResponse]:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        check_project_access(project, current_user)

        tasks, total = self.task_repository.get_filtered(
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            search=search,
            page=page,
            per_page=per_page,
        )

        return PaginatedResponse(
            data=[_to_response(task) for task in tasks],
            pagination=PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=math.ceil(total / per_page),
            ),
        )

    def create_task(
        self,
        project_id: int,
        task_data: TaskCreate,
        current_user: User,
    ) -> TaskResponse:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        check_project_access(project, current_user)

        if task_data.assigneeId is not None:
            _ensure_project_member(project, task_data.assigneeId)

        task = self.task_repository.create(
            project_id=project_id,
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            assignee_id=task_data.assigneeId,
            reporter_id=current_user.id,
            due_date=task_data.dueDate,
            tags=task_data.tags,
        )

        self.activity_repository.create(
            type="task_created",
            user_id=current_user.id,
            project_id=project_id,
            task_id=task.id,
            message=render_activity_message(
                "task_created", actor=current_user.name, task_title=task.title
            ),
        )

        if task.assignee_id is not None:
            self.activity_repository.create(
                type="task_assigned",
                user_id=current_user.id,
                project_id=project_id,
                task_id=task.id,
                message=render_activity_message(
                    "task_assigned",
                    actor=current_user.name,
                    assignee_name=task.assignee.name,
                ),
            )

        return _to_response(task)

    def get_task_by_id(self, task_id: int, current_user: User) -> TaskDetailResponse:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException()

        check_task_access(task, current_user)

        return _to_detail_response(task)

    def update_task(
        self,
        task_id: int,
        task_update: TaskUpdate,
        current_user: User,
    ) -> TaskDetailResponse:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException()

        if not _can_edit_task(task, current_user):
            raise TaskEditPermissionException()

        update_fields = task_update.model_dump(exclude_unset=True)
        updated_task = self.task_repository.update(task_id, update_fields)

        return _to_detail_response(updated_task)

    def update_task_status(
        self,
        task_id: int,
        request: TaskStatusUpdateRequest,
        current_user: User,
    ) -> TaskStatusUpdateResponse:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException()

        if not _can_edit_task(task, current_user):
            raise TaskEditPermissionException()

        if (
            current_user.role == "developer"
            and task.status == "done"
            and request.status != "done"
        ):
            raise CannotReopenCompletedTaskException()

        old_status = task.status
        updated_task = self.task_repository.update(task_id, {"status": request.status})

        if updated_task.status != old_status:
            self._log_status_change(updated_task, current_user)

        return TaskStatusUpdateResponse(
            id=updated_task.id,
            status=updated_task.status,
            updatedAt=updated_task.updated_at,
        )

    def update_task_priority(
        self,
        task_id: int,
        request: TaskPriorityUpdateRequest,
        current_user: User,
    ) -> TaskPriorityUpdateResponse:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException()

        if not _can_edit_task(task, current_user):
            raise TaskEditPermissionException()

        old_priority = task.priority
        updated_task = self.task_repository.update(
            task_id, {"priority": request.priority}
        )

        if updated_task.priority != old_priority:
            self.activity_repository.create(
                type="priority_changed",
                user_id=current_user.id,
                project_id=updated_task.project_id,
                task_id=updated_task.id,
                message=render_activity_message(
                    "priority_changed",
                    actor=current_user.name,
                    new_priority_label=PRIORITY_LABELS.get(
                        updated_task.priority, updated_task.priority.title()
                    ),
                ),
            )

        return TaskPriorityUpdateResponse(
            id=updated_task.id,
            priority=updated_task.priority,
            updatedAt=updated_task.updated_at,
        )

    def update_task_assignee(
        self,
        task_id: int,
        request: TaskAssigneeUpdateRequest,
        current_user: User,
    ) -> TaskAssigneeUpdateResponse:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException()

        assignee = None
        if request.assigneeId is not None:
            assignee = _ensure_project_member(task.project, request.assigneeId)

        updated_task = self.task_repository.update(
            task_id, {"assignee_id": request.assigneeId}
        )

        if assignee is not None:
            self.activity_repository.create(
                type="task_assigned",
                user_id=current_user.id,
                project_id=updated_task.project_id,
                task_id=updated_task.id,
                message=render_activity_message(
                    "task_assigned", actor=current_user.name, assignee_name=assignee.name
                ),
            )

        return TaskAssigneeUpdateResponse(
            id=updated_task.id,
            assigneeId=updated_task.assignee_id,
            assignee=UserSummary.model_validate(assignee) if assignee else None,
            updatedAt=updated_task.updated_at,
        )

    def update_task_due_date(
        self,
        task_id: int,
        request: TaskDueDateUpdateRequest,
        current_user: User,
    ) -> TaskDueDateUpdateResponse:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException()

        if not _can_edit_task(task, current_user):
            raise TaskEditPermissionException()

        updated_task = self.task_repository.update(
            task_id, {"due_date": request.dueDate}
        )

        return TaskDueDateUpdateResponse(
            id=updated_task.id,
            dueDate=updated_task.due_date,
            updatedAt=updated_task.updated_at,
        )

    def delete_task(self, task_id: int, current_user: User) -> None:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException()

        if not _can_edit_task(task, current_user):
            raise TaskDeletePermissionException()

        # Logged before the delete, not after: once the row is gone, an
        # activity referencing task_id would violate the foreign key.
        self.activity_repository.create(
            type="task_deleted",
            user_id=current_user.id,
            project_id=task.project_id,
            task_id=None,
            message=render_activity_message(
                "task_deleted", actor=current_user.name, task_title=task.title
            ),
        )

        self.task_repository.delete(task_id)

    def get_kanban_board(
        self,
        project_id: int,
        current_user: User,
    ) -> KanbanBoardResponse:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        check_project_access(project, current_user)

        tasks = self.task_repository.get_by_project_ordered(project_id)

        columns: dict[str, list[KanbanTask]] = {status: [] for status in TASK_STATUSES}
        for task in tasks:
            if task.status in columns:
                columns[task.status].append(_to_kanban_task(task))

        return KanbanBoardResponse(
            projectId=project_id,
            columns={
                status: KanbanColumn(label=_COLUMN_LABELS[status], tasks=column_tasks)
                for status, column_tasks in columns.items()
            },
        )

    def move_task(
        self,
        task_id: int,
        request: MoveTaskRequest,
        current_user: User,
    ) -> MoveTaskResponse:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException()

        if not _can_edit_task(task, current_user):
            raise CannotMoveTaskException()

        if (
            current_user.role == "developer"
            and task.status == "done"
            and request.status != "done"
        ):
            raise CannotReopenTaskViaMoveException()

        old_status = task.status
        updated_task = self.task_repository.move(
            task, request.status, request.columnOrder
        )

        if updated_task.status != old_status:
            self._log_status_change(updated_task, current_user)

        return MoveTaskResponse(
            id=updated_task.id,
            status=updated_task.status,
            columnOrder=updated_task.column_order,
            updatedAt=updated_task.updated_at,
        )

    def get_kanban_stats(
        self,
        project_id: int,
        current_user: User,
    ) -> KanbanStatsResponse:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        check_project_access(project, current_user)

        counts = count_by_status(project.tasks)
        total = len(project.tasks)

        def stat(count: int) -> ColumnStat:
            percentage = round((count / total) * 100) if total else 0
            return ColumnStat(count=count, percentage=percentage)

        progress = round((counts["done"] / total) * 100) if total else 0

        return KanbanStatsResponse(
            projectId=project_id,
            total=total,
            todo=stat(counts["todo"]),
            in_progress=stat(counts["in_progress"]),
            testing=stat(counts["testing"]),
            done=stat(counts["done"]),
            progress=progress,
        )

    def _log_status_change(self, task: Task, current_user: User) -> None:
        if task.status == "done":
            self.activity_repository.create(
                type="task_completed",
                user_id=current_user.id,
                project_id=task.project_id,
                task_id=task.id,
                message=render_activity_message(
                    "task_completed", actor=current_user.name, task_title=task.title
                ),
            )
        else:
            self.activity_repository.create(
                type="status_changed",
                user_id=current_user.id,
                project_id=task.project_id,
                task_id=task.id,
                message=render_activity_message(
                    "status_changed",
                    actor=current_user.name,
                    new_status_label=STATUS_LABELS.get(task.status, task.status.title()),
                ),
            )


def _can_edit_task(task: Task, current_user: User) -> bool:
    if current_user.role in _TASK_EDIT_ROLES:
        return True
    return current_user.id in (task.assignee_id, task.reporter_id)


def _ensure_project_member(project: Project, user_id: int) -> User:
    member = next((m for m in project.members if m.id == user_id), None)
    if member is None:
        raise AssigneeNotProjectMemberException()
    return member


def _to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        projectId=task.project_id,
        assigneeId=task.assignee_id,
        reporterId=task.reporter_id,
        dueDate=task.due_date,
        tags=task.tags,
        commentsCount=len(task.comments),
        columnOrder=task.column_order,
        createdAt=task.created_at,
        updatedAt=task.updated_at,
    )


def _to_kanban_task(task: Task) -> KanbanTask:
    return KanbanTask(
        id=task.id,
        title=task.title,
        status=task.status,
        priority=task.priority,
        assigneeId=task.assignee_id,
        assignee=UserSummary.model_validate(task.assignee) if task.assignee else None,
        reporterId=task.reporter_id,
        dueDate=task.due_date,
        tags=task.tags,
        commentsCount=len(task.comments),
        columnOrder=task.column_order,
    )


def _to_detail_response(task: Task) -> TaskDetailResponse:
    return TaskDetailResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        projectId=task.project_id,
        projectName=task.project.name,
        assigneeId=task.assignee_id,
        assignee=UserSummary.model_validate(task.assignee) if task.assignee else None,
        reporterId=task.reporter_id,
        reporter=UserSummary.model_validate(task.reporter),
        dueDate=task.due_date,
        tags=task.tags,
        commentsCount=len(task.comments),
        columnOrder=task.column_order,
        createdAt=task.created_at,
        updatedAt=task.updated_at,
    )
