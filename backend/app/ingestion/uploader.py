import logging
from datetime import datetime
from pathlib import Path

from app.application.settings import AppSettings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024
MAX_FILE_SIZE = 500 * 1024 * 1024
TMP_DIR = Path("./tmp")


def save_file(file, settings=None):
    """
    Guarda un ZIP subido en disco usando lectura por bloques.
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        logger.error("Archivo invalido: %s. Debe ser .zip", file.filename)
        raise ValueError(f"El archivo debe ser .zip, recibio: {file.filename}")

    runtime_settings = settings or AppSettings.from_env()
    chunk_size = runtime_settings.upload_chunk_size if settings else CHUNK_SIZE
    max_file_size = runtime_settings.max_file_size if settings else MAX_FILE_SIZE
    tmp_root = runtime_settings.tmp_dir if settings else TMP_DIR

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = tmp_root / timestamp
    tmp_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename).name
    file_path = tmp_dir / safe_name
    total_bytes = 0

    try:
        file.file.seek(0)
        with open(file_path, "wb") as file_obj:
            while True:
                chunk = file.file.read(chunk_size)
                if not chunk:
                    break
                file_obj.write(chunk)
                total_bytes += len(chunk)
                if total_bytes > max_file_size:
                    raise ValueError(
                        f"El archivo supera el limite permitido ({max_file_size} bytes)"
                    )

        if total_bytes == 0:
            raise ValueError("El archivo esta vacio")

        logger.info("Archivo guardado exitosamente: %s (%s bytes)", file_path, total_bytes)
        return str(file_path)
    except Exception as exc:
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        logger.error("Error guardando archivo: %s", exc)
        raise
