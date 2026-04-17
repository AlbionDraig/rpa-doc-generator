import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.download import router as download_router
from app.api.routes.generate import router as generate_router
from app.api.routes.quality import router as quality_router
from app.api.routes.system import router as system_router
from app.application.settings import AppSettings
from app.limits import ConcurrencyLimiter, EndpointRateLimitMiddleware
from app.observability import ObservabilityMiddleware, configure_logging

load_dotenv()
settings = AppSettings.from_env()

configure_logging(settings)
logger = logging.getLogger(__name__)

def create_app():
    app_instance = FastAPI(
        title=settings.app_title,
        description=settings.app_description,
        version=settings.app_version,
        docs_url=None,
        redoc_url=None,
    )

    app_instance.state.settings = settings
    app_instance.state.logger = logger
    app_instance.state.generation_limiter = ConcurrencyLimiter(
        limit=settings.max_concurrent_generations,
        acquire_timeout_seconds=settings.generation_acquire_timeout_seconds,
    )

    app_instance.add_middleware(ObservabilityMiddleware, logger=logger)
    app_instance.add_middleware(
        EndpointRateLimitMiddleware,
        logger=logger,
        enabled=settings.api_rate_limit_enabled,
        limit=settings.api_rate_limit_max_requests,
        window_seconds=settings.api_rate_limit_window_seconds,
        protected_paths={"/generate/", "/quality/"},
    )

    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.tmp_dir.mkdir(parents=True, exist_ok=True)
    settings.static_dir.mkdir(parents=True, exist_ok=True)

    app_instance.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

    app_instance.include_router(generate_router)
    app_instance.include_router(quality_router)
    app_instance.include_router(download_router)
    app_instance.include_router(system_router)

    return app_instance


app = create_app()


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_favicon_url="/favicon.ico",
    )


@app.get("/docs/oauth2-redirect", include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=f"{app.title} - ReDoc",
        redoc_favicon_url="/favicon.ico",
    )

logger.info("=" * 60)
logger.info("RPA Doc Generator - API iniciada")
logger.info("=" * 60)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/static/favicon.ico")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.app_log_level,
        access_log=settings.app_access_log,
    )
