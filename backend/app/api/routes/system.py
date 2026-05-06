from datetime import datetime

from fastapi import APIRouter, Request

from app.api.contracts import HealthResponse, RootResponse
from app.api.deps import get_settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    settings = get_settings(request)
    return {
        "status": "healthy",
        "app": settings.app_title,
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/", response_model=RootResponse)
async def root(request: Request):
    settings = get_settings(request)
    return {
        "message": f"{settings.app_title} API",
        "version": settings.app_version,
        "docs": f"{settings.public_base_url}/docs",
        "redoc": f"{settings.public_base_url}/redoc",
        "health": f"{settings.public_base_url}/health",
    }
