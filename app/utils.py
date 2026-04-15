"""
Utilidades comunes para RPA Doc Generator
"""
import logging
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def format_size(bytes_size):
    """Convierte bytes a formato legible."""
    if bytes_size is None:
        return "0B"
    
    bytes_size = int(bytes_size)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f}TB"


def sanitize_filename(filename):
    """Sanitiza un nombre de archivo removiendo caracteres inválidos."""
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def save_json(data, filepath):
    """Guarda datos en formato JSON."""
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON guardado en: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Error guardando JSON: {str(e)}")
        raise


def load_json(filepath):
    """Carga datos desde un archivo JSON."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando JSON: {str(e)}")
        raise


def get_session_id():
    """Genera un ID único para la sesión."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def create_output_directory(session_id):
    """Crea un directorio de salida para una sesión."""
    from app.config import OUTPUT_DIR
    output_dir = OUTPUT_DIR / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def clean_old_sessions(days=7):
    """
    Limpia sesiones antiguas de más de X días.
    
    Args:
        days: Número de días después del cual limpiar
    """
    from app.config import OUTPUT_DIR, TEMP_DIR
    import shutil
    from datetime import timedelta
    
    now = datetime.now()
    cutoff_time = now - timedelta(days=days)
    
    for directory in [OUTPUT_DIR, TEMP_DIR]:
        if directory.exists():
            for item in directory.iterdir():
                if item.is_dir():
                    try:
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        if mtime < cutoff_time:
                            shutil.rmtree(item)
                            logger.info(f"Directorio limpiado: {item}")
                    except Exception as e:
                        logger.warning(f"Error limpiando {item}: {str(e)}")
