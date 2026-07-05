import math

from app.models.project import Project
from app.models.user import User
from app.repositories.activity_repository import ActivityRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import DataListResponse, PaginatedResponse, PaginationMeta
from app.schemas.project import (
    AddMemberRequest,
    ProjectCreate,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
    TaskCounts,
    UpdateMemberRoleRequest,
    UpdateMemberRoleResponse,
)
from app.core.activity_templates import STATUS_LABELS, render_activity_message
from app.core.exceptions import (
    CannotRemoveOwnerException,
    InsufficientPermissionsException,
    NotAProjectMemberException,
    ProjectNotFoundException,
    UserAlreadyMemberException,
    UserNotFoundException,
)
from app.services.access_control import PRIVILEGED_ROLES, check_project_access
from app.services.task_stats import count_by_status


class ProjectService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        user_repository: UserRepository,
        activity_repository: ActivityRepository,
    ):
        self.project_repository = project_repository
        self.user_repository = user_repository
        self.activity_repository = activity_repository

    def create_project(
        self,
        project_data: ProjectCreate,
        current_user: User,
    ) -> ProjectResponse:
        project = self.project_repository.create(
            name=project_data.name,
            description=project_data.description,
            status=project_data.status,
            priority=project_data.priority,
            color=project_data.color,
            due_date=project_data.dueDate,
            tags=project_data.tags,
            owner=current_user,
        )

        self.activity_repository.create(
            type="project_created",
            user_id=current_user.id,
            project_id=project.id,
            message=render_activity_message(
                "project_created", actor=current_user.name, project_name=project.name
            ),
        )

        return _to_response(project)

    def list_projects(
        self,
        current_user: User,
        status: str | None,
        search: str | None,
        priority: str | None,
        page: int,
        per_page: int,
    ) -> PaginatedResponse[ProjectResponse]:
        is_privileged = current_user.role in PRIVILEGED_ROLES
        member_user_id = None if is_privileged else current_user.id

        projects, total = self.project_repository.get_filtered(
            status=status,
            search=search,
            priority=priority,
            page=page,
            per_page=per_page,
            member_user_id=member_user_id,
        )

        return PaginatedResponse(
            data=[_to_response(project) for project in projects],
            pagination=PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=math.ceil(total / per_page),
            ),
        )

    def get_project_by_id(self, project_id: int, current_user: User) -> ProjectResponse:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        check_project_access(project, current_user)

        return _to_response(project)

    def update_project(
        self,
        project_id: int,
        project_update: ProjectUpdate,
        current_user: User,
    ) -> ProjectResponse:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        old_status = project.status
        update_fields = project_update.model_dump(exclude_unset=True)

        # ProjectUpdate uses the request's camelCase field name (dueDate) since
        # that's what the client sends; the ORM column is due_date. Every other
        # field here happens to match, so this is the one translation needed.
        if "dueDate" in update_fields:
            update_fields["due_date"] = update_fields.pop("dueDate")

        updated_project = self.project_repository.update(project_id, update_fields)

        if "status" in update_fields and update_fields["status"] != old_status:
            self.activity_repository.create(
                type="status_changed",
                user_id=current_user.id,
                project_id=updated_project.id,
                message=render_activity_message(
                    "status_changed",
                    actor=current_user.name,
                    # STATUS_LABELS only covers task statuses (todo/in_progress/...);
                    # project status (active/completed) isn't in that map, so fall
                    # back to a title-cased version of the raw value.
                    new_status_label=STATUS_LABELS.get(
                        updated_project.status,
                        updated_project.status.replace("_", " ").title(),
                    ),
                ),
            )

        return _to_response(updated_project)

    def delete_project(self, project_id: int) -> None:
        project = self.project_repository.delete(project_id)
        if not project:
            raise ProjectNotFoundException()

    def list_members(
        self,
        project_id: int,
        current_user: User,
    ) -> DataListResponse[ProjectMemberResponse]:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        check_project_access(project, current_user)

        return DataListResponse(
            data=[_to_member_response(member, project) for member in project.members]
        )

    def add_member(
        self,
        project_id: int,
        request: AddMemberRequest,
        current_user: User,
    ) -> DataListResponse[ProjectMemberResponse]:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        user = self.user_repository.get_by_id(request.user_id)
        if not user:
            raise UserNotFoundException()

        if any(member.id == user.id for member in project.members):
            raise UserAlreadyMemberException()

        project = self.project_repository.add_member(project, user)

        self.activity_repository.create(
            type="member_added",
            user_id=current_user.id,
            project_id=project.id,
            message=render_activity_message(
                "member_added", actor=current_user.name, member_name=user.name
            ),
        )

        return DataListResponse(
            data=[_to_member_response(member, project) for member in project.members]
        )

    def remove_member(
        self,
        project_id: int,
        user_id: int,
        current_user: User,
    ) -> DataListResponse[ProjectMemberResponse]:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        if project.owner_id == user_id:
            raise CannotRemoveOwnerException()

        member = next((m for m in project.members if m.id == user_id), None)
        if member is None:
            raise NotAProjectMemberException()

        removed_member_name = member.name
        project = self.project_repository.remove_member(project, member)

        self.activity_repository.create(
            type="member_removed",
            user_id=current_user.id,
            project_id=project.id,
            message=render_activity_message(
                "member_removed",
                actor=current_user.name,
                member_name=removed_member_name,
            ),
        )

        return DataListResponse(
            data=[_to_member_response(m, project) for m in project.members]
        )

    def update_member_role(
        self,
        project_id: int,
        user_id: int,
        request: UpdateMemberRoleRequest,
        current_user: User,
    ) -> UpdateMemberRoleResponse:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        member = next((m for m in project.members if m.id == user_id), None)
        if member is None:
            raise NotAProjectMemberException()

        if current_user.role == "manager" and request.role == "admin":
            raise InsufficientPermissionsException(
                "Insufficient permissions to assign this role"
            )

        updated_user = self.user_repository.update(user_id, {"role": request.role})

        return UpdateMemberRoleResponse(
            id=updated_user.id,
            name=updated_user.name,
            role=updated_user.role,
            updatedAt=updated_user.updated_at,
        )


def _to_member_response(member: User, project: Project) -> ProjectMemberResponse:
    return ProjectMemberResponse(
        id=member.id,
        name=member.name,
        email=member.email,
        role=member.role,
        avatarUrl=member.avatar_url,
        initials=member.initials,
        color=member.color,
        status=member.status,
        department=member.department,
        isOwner=member.id == project.owner_id,
    )


def _compute_task_counts(project: Project) -> TaskCounts:
    by_status = count_by_status(project.tasks)

    return TaskCounts(
        total=len(project.tasks),
        todo=by_status["todo"],
        inProgress=by_status["in_progress"],
        testing=by_status["testing"],
        done=by_status["done"],
    )


def _to_response(project: Project) -> ProjectResponse:
    task_counts = _compute_task_counts(project)
    progress = (
        round((task_counts.done / task_counts.total) * 100)
        if task_counts.total
        else 0
    )

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        priority=project.priority,
        color=project.color,
        progress=progress,
        startDate=project.start_date,
        dueDate=project.due_date,
        ownerId=project.owner_id,
        memberIds=[member.id for member in project.members],
        tags=project.tags,
        tasksCount=task_counts,
        createdAt=project.created_at,
        updatedAt=project.updated_at,
    )
