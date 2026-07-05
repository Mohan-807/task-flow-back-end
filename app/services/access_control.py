from app.core.exceptions import ProjectAccessDeniedException, TaskAccessDeniedException
from app.models.project import Project
from app.models.task import Task
from app.models.user import User

PRIVILEGED_ROLES = {"admin", "manager"}


def check_project_access(project: Project, current_user: User) -> None:
    is_privileged = current_user.role in PRIVILEGED_ROLES
    is_member = any(member.id == current_user.id for member in project.members)
    if not is_privileged and not is_member:
        raise ProjectAccessDeniedException()


def check_task_access(task: Task, current_user: User) -> None:
    is_privileged = current_user.role in PRIVILEGED_ROLES
    is_member = any(member.id == current_user.id for member in task.project.members)
    if not is_privileged and not is_member:
        raise TaskAccessDeniedException()
