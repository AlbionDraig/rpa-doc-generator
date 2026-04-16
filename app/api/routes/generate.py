from fastapi import APIRouter, HTTPException, Request, UploadFile

from app.api.deps import get_logger, get_settings
from app.application.use_cases.generate_sdd import run_generate_sdd

router = APIRouter()


@router.post("/generate/")
async def generate(file: UploadFile, request: Request):
    settings = get_settings(request)
    logger = get_logger(request)
    try:
        return run_generate_sdd(file, settings, logger)
    except ValueError as exc:
        logger.error("[ERROR] Validacion: %s", exc)
        raise HTTPException(status_code=400, detail=f"Error de validacion: {exc}") from exc
    except FileNotFoundError as exc:
        logger.error("[ERROR] Archivo no encontrado: %s", exc)
        raise HTTPException(status_code=404, detail=f"No encontrado: {exc}") from exc
    except Exception as exc:
        logger.error("[ERROR] Inesperado: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}") from exc
