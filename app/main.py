from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.constants import API_DESCRIPTION
from app.core.exception_handlers import register_exception_handlers

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
register_exception_handlers(app)
app.include_router(api_router)