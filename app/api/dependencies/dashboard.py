from app.api.dependencies.activities import ActivityRepositoryDep
from app.api.dependencies.projects import ProjectRepositoryDep
from app.api.dependencies.tasks import TaskRepositoryDep
from app.api.dependencies.users import UserRepositoryDep
from app.services.dashboard_service import DashboardService


def get_dashboard_service(
    project_repository: ProjectRepositoryDep,
    task_repository: TaskRepositoryDep,
    user_repository: UserRepositoryDep,
    activity_repository: ActivityRepositoryDep,
) -> DashboardService:
    return DashboardService(
        project_repository, task_repository, user_repository, activity_repository
    )
