from datetime import datetime

from fastapi import APIRouter, Request

from app.api.deps import get_settings

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    settings = get_settings(request)
    return {
        "status": "healthy",
        "app": settings.app_title,
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/")
async def root(request: Request):
    settings = get_settings(request)
    return {
        "message": f"{settings.app_title} API",
        "version": settings.app_version,
        "docs": f"{settings.public_base_url}/docs",
        "redoc": f"{settings.public_base_url}/redoc",
        "health": f"{settings.public_base_url}/health",
    }
