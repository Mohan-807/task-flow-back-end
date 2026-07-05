from fastapi import APIRouter

from app.api.dependencies.types import CurrentUserDep, DashboardServiceDep
from app.schemas.activity import ActivityResponse
from app.schemas.common import DataListResponse
from app.schemas.dashboard import (
    DashboardStatsResponse,
    RecentProjectResponse,
    RecentTaskResponse,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    current_user: CurrentUserDep,
    dashboard_service: DashboardServiceDep,
):
    return dashboard_service.get_stats(current_user)

@router.get("/recent-projects", response_model=DataListResponse[RecentProjectResponse])
def get_recent_projects(
    current_user: CurrentUserDep,
    dashboard_service: DashboardServiceDep,
):
    return dashboard_service.get_recent_projects(current_user)

@router.get("/recent-tasks", response_model=DataListResponse[RecentTaskResponse])
def get_recent_tasks(
    current_user: CurrentUserDep,
    dashboard_service: DashboardServiceDep,
):
    return dashboard_service.get_recent_tasks(current_user)

@router.get("/activities", response_model=DataListResponse[ActivityResponse])
def get_dashboard_activities(
    current_user: CurrentUserDep,
    dashboard_service: DashboardServiceDep,
):
    return dashboard_service.get_activity_feed(current_user)
