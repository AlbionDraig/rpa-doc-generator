import os
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def save_file(file):
    """
    Guarda un archivo ZIP subido en la carpeta temporal.
    
    Args:
        file: UploadFile de FastAPI
        
    Returns:
        str: Ruta donde se guardó el archivo
        
    Raises:
        ValueError: Si el archivo no es válido o no es ZIP
    """
    # Validar que sea un archivo ZIP
    if not file.filename.endswith('.zip'):
        logger.error(f"Archivo inválido: {file.filename}. Debe ser .zip")
        raise ValueError(f"El archivo debe ser .zip, recibió: {file.filename}")
    
    # Crear carpeta temporal con timestamp para evitar conflictos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = Path("./tmp") / timestamp
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = tmp_dir / file.filename
    
    try:
        with open(file_path, "wb") as f:
            content = file.file.read()
            if not content:
                raise ValueError("El archivo está vacío")
            f.write(content)
        
        logger.info(f"Archivo guardado exitosamente: {file_path}")
        return str(file_path)
    
    except Exception as e:
        logger.error(f"Error guardando archivo: {str(e)}")
        raise
