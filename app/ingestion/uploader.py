import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CHUNK_SIZE = int(os.getenv("UPLOAD_CHUNK_SIZE", str(1024 * 1024)))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(500 * 1024 * 1024)))
TMP_DIR = Path(os.getenv("TMP_DIR", "./tmp"))


def save_file(file):
    """
    Guarda un ZIP subido en disco usando lectura por bloques.
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        logger.error("Archivo invalido: %s. Debe ser .zip", file.filename)
        raise ValueError(f"El archivo debe ser .zip, recibio: {file.filename}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = TMP_DIR / timestamp
    tmp_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename).name
    file_path = tmp_dir / safe_name
    total_bytes = 0

    try:
        file.file.seek(0)
        with open(file_path, "wb") as file_obj:
            while True:
                chunk = file.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                file_obj.write(chunk)
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE:
                    raise ValueError(
                        f"El archivo supera el limite permitido ({MAX_FILE_SIZE} bytes)"
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
