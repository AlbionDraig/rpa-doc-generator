import zipfile
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def extract_project(zip_path):
    """
    Extrae el contenido del ZIP del bot de Automation Anywhere.
    
    Args:
        zip_path (str): Ruta del archivo ZIP
        
    Returns:
        str: Ruta de la carpeta extraída
        
    Raises:
        FileNotFoundError: Si el archivo ZIP no existe
        zipfile.BadZipFile: Si el archivo no es un ZIP válido
    """
    try:
        zip_path = Path(zip_path)
        
        if not zip_path.exists():
            logger.error(f"Archivo ZIP no encontrado: {zip_path}")
            raise FileNotFoundError(f"El archivo {zip_path} no existe")
        
        # Crear carpeta para extraer con el nombre del ZIP sin extensión
        extract_path = zip_path.parent / zip_path.stem
        extract_path.mkdir(parents=True, exist_ok=True)
        
        # Validar que sea un ZIP válido y extraer
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Validar integridad del ZIP
            bad_file = zip_ref.testzip()
            if bad_file:
                logger.error(f"ZIP corrompido: {bad_file}")
                raise zipfile.BadZipFile(f"El archivo ZIP está corrompido: {bad_file}")
            
            zip_ref.extractall(extract_path)
        
        logger.info(f"Proyecto extraído exitosamente en: {extract_path}")
        return str(extract_path)
    
    except zipfile.BadZipFile as e:
        logger.error(f"Error de ZIP: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error extrayendo proyecto: {str(e)}")
        raise
