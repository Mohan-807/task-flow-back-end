from typing import Annotated

from fastapi import Depends

from app.api.dependencies.activities import ActivityRepositoryDep
from app.api.dependencies.db import DBSession
from app.api.dependencies.tasks import TaskRepositoryDep
from app.repositories.comment_repository import CommentRepository
from app.services.comment_service import CommentService


def get_comment_repository(
    db: DBSession,
) -> CommentRepository:
    return CommentRepository(db)


CommentRepositoryDep = Annotated[CommentRepository, Depends(get_comment_repository)]


def get_comment_service(
    comment_repository: CommentRepositoryDep,
    task_repository: TaskRepositoryDep,
    activity_repository: ActivityRepositoryDep,
) -> CommentService:
    return CommentService(comment_repository, task_repository, activity_repository)
