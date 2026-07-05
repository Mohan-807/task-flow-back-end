import math

from app.models.project import Project
from app.models.user import User
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
from app.core.exceptions import (
    CannotRemoveOwnerException,
    InsufficientPermissionsException,
    NotAProjectMemberException,
    ProjectAccessDeniedException,
    ProjectNotFoundException,
    UserAlreadyMemberException,
    UserNotFoundException,
)

_PRIVILEGED_ROLES = {"admin", "manager"}

# Placeholder until Tasks (Phase 5) exists — there is no Task model yet, so
# every project's task counts and progress are genuinely zero, not estimated.
_ZERO_TASK_COUNTS = TaskCounts(total=0, todo=0, inProgress=0, testing=0, done=0)


class ProjectService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        user_repository: UserRepository,
    ):
        self.project_repository = project_repository
        self.user_repository = user_repository

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
        is_privileged = current_user.role in _PRIVILEGED_ROLES
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

        _check_project_access(project, current_user)

        return _to_response(project)

    def update_project(
        self,
        project_id: int,
        project_update: ProjectUpdate,
    ) -> ProjectResponse:
        if not self.project_repository.get_by_id(project_id):
            raise ProjectNotFoundException()

        update_fields = project_update.model_dump(exclude_unset=True)

        # ProjectUpdate uses the request's camelCase field name (dueDate) since
        # that's what the client sends; the ORM column is due_date. Every other
        # field here happens to match, so this is the one translation needed.
        if "dueDate" in update_fields:
            update_fields["due_date"] = update_fields.pop("dueDate")

        updated_project = self.project_repository.update(project_id, update_fields)
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

        _check_project_access(project, current_user)

        return DataListResponse(
            data=[_to_member_response(member, project) for member in project.members]
        )

    def add_member(
        self,
        project_id: int,
        request: AddMemberRequest,
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

        return DataListResponse(
            data=[_to_member_response(member, project) for member in project.members]
        )

    def remove_member(
        self,
        project_id: int,
        user_id: int,
    ) -> DataListResponse[ProjectMemberResponse]:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        if project.owner_id == user_id:
            raise CannotRemoveOwnerException()

        member = next((m for m in project.members if m.id == user_id), None)
        if member is None:
            raise NotAProjectMemberException()

        project = self.project_repository.remove_member(project, member)

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


def _check_project_access(project: Project, current_user: User) -> None:
    is_privileged = current_user.role in _PRIVILEGED_ROLES
    is_member = any(member.id == current_user.id for member in project.members)
    if not is_privileged and not is_member:
        raise ProjectAccessDeniedException()


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


def _to_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        status=project.status,
        priority=project.priority,
        color=project.color,
        progress=0,
        startDate=project.start_date,
        dueDate=project.due_date,
        ownerId=project.owner_id,
        memberIds=[member.id for member in project.members],
        tags=project.tags,
        tasksCount=_ZERO_TASK_COUNTS,
        createdAt=project.created_at,
        updatedAt=project.updated_at,
    )
