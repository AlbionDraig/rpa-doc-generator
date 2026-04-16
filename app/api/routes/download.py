from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.api.deps import get_logger, get_settings
from app.application.use_cases.download_artifact import resolve_download_file

router = APIRouter()


@router.get("/download/{session_id}/{file_type}")
async def download_file(session_id: str, file_type: str, request: Request):
    settings = get_settings(request)
    logger = get_logger(request)
    output_dir = settings.output_dir / session_id

    try:
        file_path = resolve_download_file(output_dir, file_type)
        if file_path is None:
            logger.warning("[WARNING] Tipo de archivo invalido: %s", file_type)
            raise HTTPException(status_code=400, detail="Tipo de archivo invalido")

        if not file_path.exists():
            logger.warning("[WARNING] Archivo no encontrado: %s - Sesion: %s", file_type, session_id)
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

        logger.info("[DOWNLOAD] %s - Sesion: %s", file_type, session_id)
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[ERROR] Descargando archivo: %s - Sesion: %s", exc, session_id)
        raise HTTPException(status_code=500, detail="Error al descargar archivo") from exc
