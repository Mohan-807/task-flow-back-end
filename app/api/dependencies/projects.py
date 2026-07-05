from typing import Annotated

from fastapi import Depends

from app.api.dependencies.activities import ActivityRepositoryDep
from app.api.dependencies.db import DBSession
from app.api.dependencies.users import UserRepositoryDep
from app.repositories.project_repository import ProjectRepository
from app.services.project_service import ProjectService


def get_project_repository(
    db: DBSession,
) -> ProjectRepository:
    return ProjectRepository(db)


ProjectRepositoryDep = Annotated[ProjectRepository, Depends(get_project_repository)]


def get_project_service(
    project_repository: ProjectRepositoryDep,
    user_repository: UserRepositoryDep,
    activity_repository: ActivityRepositoryDep,
) -> ProjectService:
    return ProjectService(project_repository, user_repository, activity_repository)
