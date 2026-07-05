from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.repositories.activity_repository import ActivityRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.activity import ActivityResponse
from app.schemas.common import DataListResponse
from app.schemas.dashboard import (
    DashboardStatsResponse,
    MemberAvatar,
    RecentProjectResponse,
    RecentTaskResponse,
)
from app.schemas.user import UserSummary
from app.services.access_control import PRIVILEGED_ROLES
from app.services.task_stats import count_by_status

_RECENT_PROJECTS_LIMIT = 4
_RECENT_TASKS_LIMIT = 7
_ACTIVITY_FEED_LIMIT = 8


class DashboardService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        task_repository: TaskRepository,
        user_repository: UserRepository,
        activity_repository: ActivityRepository,
    ):
        self.project_repository = project_repository
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.activity_repository = activity_repository

    def get_stats(self, current_user: User) -> DashboardStatsResponse:
        visible_projects = self._get_visible_projects(current_user)

        active_projects = sum(1 for p in visible_projects if p.status == "active")
        all_tasks = [task for project in visible_projects for task in project.tasks]
        total_tasks = len(all_tasks)
        done_tasks = sum(1 for task in all_tasks if task.status == "done")
        completion_rate = round((done_tasks / total_tasks) * 100) if total_tasks else 0

        return DashboardStatsResponse(
            activeProjects=active_projects,
            totalTasks=total_tasks,
            teamMembers=self.user_repository.count_all(),
            completionRate=completion_rate,
        )

    def get_recent_projects(
        self, current_user: User
    ) -> DataListResponse[RecentProjectResponse]:
        member_user_id = self._member_scope(current_user)
        projects = self.project_repository.get_recent(
            member_user_id, _RECENT_PROJECTS_LIMIT
        )

        return DataListResponse(data=[_to_recent_project(p) for p in projects])

    def get_recent_tasks(self, current_user: User) -> DataListResponse[RecentTaskResponse]:
        project_ids = self._visible_project_ids(current_user)
        tasks = self.task_repository.get_recent(project_ids, _RECENT_TASKS_LIMIT)

        return DataListResponse(data=[_to_recent_task(t) for t in tasks])

    def get_activity_feed(self, current_user: User) -> DataListResponse[ActivityResponse]:
        project_ids = self._visible_project_ids(current_user)
        activities, _ = self.activity_repository.get_filtered(
            visible_project_ids=project_ids, page=1, per_page=_ACTIVITY_FEED_LIMIT
        )

        return DataListResponse(
            data=[
                ActivityResponse(
                    id=a.id,
                    type=a.type,
                    userId=a.user_id,
                    user=UserSummary.model_validate(a.user),
                    projectId=a.project_id,
                    taskId=a.task_id,
                    message=a.message,
                    createdAt=a.created_at,
                )
                for a in activities
            ]
        )

    def _is_privileged(self, current_user: User) -> bool:
        return current_user.role in PRIVILEGED_ROLES

    def _member_scope(self, current_user: User) -> int | None:
        return None if self._is_privileged(current_user) else current_user.id

    def _get_visible_projects(self, current_user: User) -> list[Project]:
        if self._is_privileged(current_user):
            return self.project_repository.get_all()
        return list(current_user.projects)

    def _visible_project_ids(self, current_user: User) -> list[int] | None:
        if self._is_privileged(current_user):
            return None
        return [p.id for p in current_user.projects]


def _to_recent_project(project: Project) -> RecentProjectResponse:
    by_status = count_by_status(project.tasks)
    total = len(project.tasks)
    progress = round((by_status["done"] / total) * 100) if total else 0

    return RecentProjectResponse(
        id=project.id,
        name=project.name,
        status=project.status,
        priority=project.priority,
        color=project.color,
        progress=progress,
        dueDate=project.due_date,
        tasksCount={
            "total": total,
            "todo": by_status["todo"],
            "inProgress": by_status["in_progress"],
            "testing": by_status["testing"],
            "done": by_status["done"],
        },
        members=[
            MemberAvatar(
                id=m.id, initials=m.initials, color=m.color, avatarUrl=m.avatar_url
            )
            for m in project.members
        ],
        updatedAt=project.updated_at,
    )


def _to_recent_task(task: Task) -> RecentTaskResponse:
    return RecentTaskResponse(
        id=task.id,
        title=task.title,
        projectId=task.project_id,
        projectName=task.project.name,
        status=task.status,
        priority=task.priority,
        dueDate=task.due_date,
        commentsCount=len(task.comments),
        assigneeId=task.assignee_id,
        assignee=UserSummary.model_validate(task.assignee) if task.assignee else None,
        updatedAt=task.updated_at,
    )
