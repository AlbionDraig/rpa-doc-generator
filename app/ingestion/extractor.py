import logging
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_project(zip_path):
    """
    Extrae de forma segura el contenido del ZIP del bot.
    """
    try:
        zip_path = Path(zip_path)
        if not zip_path.exists():
            logger.error("Archivo ZIP no encontrado: %s", zip_path)
            raise FileNotFoundError(f"El archivo {zip_path} no existe")

        extract_path = zip_path.parent / zip_path.stem
        extract_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            bad_file = zip_ref.testzip()
            if bad_file:
                logger.error("ZIP corrompido: %s", bad_file)
                raise zipfile.BadZipFile(f"El archivo ZIP esta corrompido: {bad_file}")

            for member in zip_ref.infolist():
                _validate_member_path(member.filename, extract_path)
                zip_ref.extract(member, extract_path)

        logger.info("Proyecto extraido exitosamente en: %s", extract_path)
        return str(extract_path)
    except zipfile.BadZipFile as exc:
        logger.error("Error de ZIP: %s", exc)
        raise
    except Exception as exc:
        logger.error("Error extrayendo proyecto: %s", exc)
        raise


def _validate_member_path(member_name, extract_path):
    destination = (extract_path / member_name).resolve()
    root = extract_path.resolve()
    if root not in destination.parents and destination != root:
        raise ValueError(f"ZIP invalido: ruta fuera del directorio destino ({member_name})")
