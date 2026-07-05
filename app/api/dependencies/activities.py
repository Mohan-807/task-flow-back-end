from typing import Annotated

from fastapi import Depends

from app.api.dependencies.db import DBSession
from app.repositories.activity_repository import ActivityRepository


def get_activity_repository(
    db: DBSession,
) -> ActivityRepository:
    return ActivityRepository(db)


ActivityRepositoryDep = Annotated[ActivityRepository, Depends(get_activity_repository)]
