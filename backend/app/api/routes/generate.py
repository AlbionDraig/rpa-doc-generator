from fastapi import APIRouter, HTTPException, Request, UploadFile

from app.api.contracts import ApiErrorResponse, ArtifactGenerationResponse
from app.api.deps import get_generation_limiter, get_logger, get_settings
from app.api.errors import build_http_error
from app.api.errors import map_exception_to_http
from app.application.use_cases.generate_sdd import run_generate_sdd

router = APIRouter()


@router.post(
    "/generate/",
    response_model=ArtifactGenerationResponse,
    responses={
        400: {"model": ApiErrorResponse, "description": "Error de validacion"},
        429: {"model": ApiErrorResponse, "description": "Rate limit excedido"},
        404: {"model": ApiErrorResponse, "description": "Archivo no encontrado"},
        503: {"model": ApiErrorResponse, "description": "Capacidad temporal agotada"},
        500: {"model": ApiErrorResponse, "description": "Error interno"},
    },
)
async def generate(file: UploadFile, request: Request):
    settings = get_settings(request)
    logger = get_logger(request)
    generation_limiter = get_generation_limiter(request)

    try:
        async with generation_limiter.slot() as acquired:
            if not acquired:
                logger.warning("Capacidad agotada para generar documentacion")
                raise build_http_error(
                    503,
                    "Capacidad temporal agotada. Intenta nuevamente en unos segundos.",
                    "capacity_exceeded",
                )

            return run_generate_sdd(file, settings, logger)
    except HTTPException:
        raise
    except Exception as exc:
        raise map_exception_to_http(exc, logger, prefix="generate") from exc
