import math

from app.models.activity import Activity
from app.models.user import User
from app.repositories.activity_repository import ActivityRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.activity import ActivityResponse
from app.schemas.common import DataListResponse, PaginatedResponse, PaginationMeta
from app.schemas.user import UserSummary
from app.core.exceptions import ProjectNotFoundException, TaskNotFoundException
from app.services.access_control import check_project_access, check_task_access


class ActivityService:
    def __init__(
        self,
        activity_repository: ActivityRepository,
        project_repository: ProjectRepository,
        task_repository: TaskRepository,
    ):
        self.activity_repository = activity_repository
        self.project_repository = project_repository
        self.task_repository = task_repository

    def list_global_activities(
        self,
        type: str | None,
        user_id: int | None,
        page: int,
        per_page: int,
    ) -> PaginatedResponse[ActivityResponse]:
        activities, total = self.activity_repository.get_filtered(
            type=type, user_id=user_id, page=page, per_page=per_page
        )

        return PaginatedResponse(
            data=[_to_response(activity) for activity in activities],
            pagination=PaginationMeta(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=math.ceil(total / per_page),
            ),
        )

    def list_project_activities(
        self,
        project_id: int,
        current_user: User,
        limit: int | None,
        page: int,
        per_page: int,
    ) -> PaginatedResponse[ActivityResponse]:
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundException()

        check_project_access(project, current_user)

        # `limit`, when the caller provides it, overrides `per_page` — see the
        # module-level note on why this endpoint documents two competing
        # "how many results" params.
        effective_per_page = limit if limit is not None else per_page

        activities, total = self.activity_repository.get_filtered(
            project_id=project_id, page=page, per_page=effective_per_page
        )

        return PaginatedResponse(
            data=[_to_response(activity) for activity in activities],
            pagination=PaginationMeta(
                total=total,
                page=page,
                per_page=effective_per_page,
                total_pages=math.ceil(total / effective_per_page),
            ),
        )

    def list_task_activities(
        self,
        task_id: int,
        current_user: User,
        limit: int,
    ) -> DataListResponse[ActivityResponse]:
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundException()

        check_task_access(task, current_user)

        activities, _ = self.activity_repository.get_filtered(
            task_id=task_id, page=1, per_page=limit
        )

        return DataListResponse(data=[_to_response(activity) for activity in activities])


def _to_response(activity: Activity) -> ActivityResponse:
    return ActivityResponse(
        id=activity.id,
        type=activity.type,
        userId=activity.user_id,
        user=UserSummary.model_validate(activity.user),
        projectId=activity.project_id,
        taskId=activity.task_id,
        message=activity.message,
        createdAt=activity.created_at,
    )
