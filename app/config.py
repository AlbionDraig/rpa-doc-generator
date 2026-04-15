"""
Configuración de la aplicación RPA Doc Generator
"""
import os
from pathlib import Path

# Directorios
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = BASE_DIR / "tmp"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

# Crear directorios si no existen
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Configuración de FastAPI
APP_TITLE = "RPA Doc Generator"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Generador automático de documentación SDD para bots de Automation Anywhere"

# Límites de archivo
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_EXTRACTION_SIZE = 1024 * 1024 * 1024  # 1 GB

# Extensiones permitidas
ALLOWED_EXTENSIONS = {'.xml', '.json', '.txt', '.yml', '.yaml', '.csv'}

# Configuración de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configuración de CORS
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
]

# Configuración por defecto
DEFAULT_PROJECT_NAME = "Proyecto sin nombre"
DEFAULT_DESCRIPTION = "Documentación auto-generada por RPA-Doc-Generator"
