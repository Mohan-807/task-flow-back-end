from app.api.dependencies.activities import ActivityRepositoryDep
from app.api.dependencies.projects import ProjectRepositoryDep
from app.api.dependencies.tasks import TaskRepositoryDep
from app.services.activity_service import ActivityService


def get_activity_service(
    activity_repository: ActivityRepositoryDep,
    project_repository: ProjectRepositoryDep,
    task_repository: TaskRepositoryDep,
) -> ActivityService:
    return ActivityService(activity_repository, project_repository, task_repository)
