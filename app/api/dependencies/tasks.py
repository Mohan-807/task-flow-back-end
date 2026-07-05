from typing import Annotated

from fastapi import Depends

from app.api.dependencies.activities import ActivityRepositoryDep
from app.api.dependencies.db import DBSession
from app.api.dependencies.projects import ProjectRepositoryDep
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService


def get_task_repository(
    db: DBSession,
) -> TaskRepository:
    return TaskRepository(db)


TaskRepositoryDep = Annotated[TaskRepository, Depends(get_task_repository)]


def get_task_service(
    task_repository: TaskRepositoryDep,
    project_repository: ProjectRepositoryDep,
    activity_repository: ActivityRepositoryDep,
) -> TaskService:
    return TaskService(task_repository, project_repository, activity_repository)
