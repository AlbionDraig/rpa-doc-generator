from fastapi import APIRouter, Request, UploadFile

from app.api.contracts import ApiErrorResponse, ArtifactGenerationResponse
from app.api.deps import get_logger, get_settings
from app.api.errors import map_exception_to_http
from app.application.use_cases.generate_quality import run_generate_quality

router = APIRouter()


@router.post(
    "/quality/",
    response_model=ArtifactGenerationResponse,
    responses={
        400: {"model": ApiErrorResponse, "description": "Error de validacion"},
        404: {"model": ApiErrorResponse, "description": "Archivo no encontrado"},
        500: {"model": ApiErrorResponse, "description": "Error interno"},
    },
)
async def quality(file: UploadFile, request: Request):
    settings = get_settings(request)
    logger = get_logger(request)
    try:
        return run_generate_quality(file, settings, logger)
    except Exception as exc:
        raise map_exception_to_http(exc, logger, prefix="quality") from exc
