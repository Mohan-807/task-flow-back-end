from fastapi import APIRouter
from app.api.v1.routers import (
    health,
    users,
    auth,
    projects,
    tasks,
    comments,
    activities,
    dashboard,
    settings,
)
from app.core.constants import API_V1_PREFIX

api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)
api_router.include_router(comments.router)
api_router.include_router(activities.router)
api_router.include_router(dashboard.router)
api_router.include_router(settings.router)