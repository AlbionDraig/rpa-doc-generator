"""
API REST Specification - RPA Doc Generator
"""

# ============================================================================
# 1. AUTENTICACIÓN
# ============================================================================

"""
Actualmente: Sin autenticación (desarrollo)

Futura implementación:
- JWT Tokens para autenticación
- API Keys para acceso programático
- OAuth2 para terceros
"""

# ============================================================================
# 2. ENDPOINTS
# ============================================================================

"""
BASE_URL: http://localhost:8000
VERSION: v1

ENDPOINTS DISPONIBLES:
"""

# POST /generate/
"""
Descripción: Genera documentación SDD para un bot
Método: POST
Content-Type: multipart/form-data

Request:
  - file (required): Archivo ZIP del bot

Response (200):
{
  "status": "success",
  "session_id": "20240415_143022_123456",
  "proyecto": "Mi Bot RPA",
  "tareas": 15,
  "archivos_xml": 10,
  "archivos_json": 5,
  "arbol": "📁 Structure...",
  "diagrama": "graph TD...",
  "sdd": "# SDD - Mi Bot RPA...",
  "archivos_salida": {
    "sdd_path": "./output/.../SDD_Mi_Bot_RPA.md",
    "diagrama_path": "./output/.../diagrama.mmp",
    "estructura_path": "./output/.../estructura.txt",
    "resumen_path": "./output/.../resumen.json"
  },
  "output_directory": "./output/20240415_143022_123456"
}

Errores:
  400: El archivo debe ser .zip
  400: El archivo está vacío
  413: Archivo demasiado grande
  500: Error interno del servidor
"""

# GET /download/{session_id}/{file_type}
"""
Descripción: Descarga un archivo generado
Método: GET

Path Parameters:
  - session_id: ID de la sesión (obtenido de /generate/)
  - file_type: Tipo de archivo (sdd, diagrama, estructura, resumen)

Response (200):
  Archivo binario para descargar

Errores:
  400: Tipo de archivo inválido
  404: Sesión o archivo no encontrado
  500: Error al descargar
"""

# GET /health
"""
Descripción: Verifica el estado de la aplicación
Método: GET

Response (200):
{
  "status": "healthy",
  "app": "RPA Doc Generator",
  "version": "1.0.0"
}
"""

# ============================================================================
# 3. ESTRUCTURA DE DATOS
# ============================================================================

"""
ProjectData:
{
  "name": str,              # Nombre del proyecto
  "path": str,              # Ruta del proyecto
  "tasks": [TaskInfo],      # Lista de tareas
  "task_count": int,        # Total de tareas
  "metadata": dict,         # Metadatos del proyecto
  "files": {
    "xml_count": int,       # Archivos XML
    "json_count": int       # Archivos JSON
  }
}

TaskInfo:
{
  "name": str,              # Nombre de la tarea
  "path": str,              # Ruta relativa
  "type": str,              # xml, json, etc.
  "size": int,              # Tamaño en bytes
  "tag": str,               # Tag del elemento (opcional)
  "attributes": dict,       # Atributos (opcional)
  "elements_count": int     # Elementos hijo (opcional)
}

Flow:
{
  "nodes": [
    {
      "id": str,            # ID único del nodo
      "name": str,          # Nombre visible
      "type": str,          # Tipo de archivo
      "order": int,         # Orden de ejecución
      "size": int           # Tamaño del archivo
    }
  ],
  "edges": [
    {
      "from": str,          # ID nodo origen
      "to": str,            # ID nodo destino
      "label": str          # Etiqueta de la conexión
    }
  ],
  "summary": {
    "total_nodes": int,
    "total_edges": int,
    "start_node": str,
    "end_node": str
  }
}
"""

# ============================================================================
# 4. CÓDIGOS DE ERROR
# ============================================================================

"""
400 Bad Request
  - El archivo debe ser .zip
  - El archivo está vacío
  - Tipo de archivo inválido
  - Datos inválidos

404 Not Found
  - Sesión no encontrada
  - Archivo no encontrado
  - Recurso no disponible

413 Payload Too Large
  - Archivo excede tamaño máximo

500 Internal Server Error
  - Error inesperado en el servidor
  - Error al procesar archivo
  - Error al generar documentación
"""

# ============================================================================
# 5. LIMITES Y CONFIGURACIÓN
# ============================================================================

"""
MAX_FILE_SIZE: 500 MB
MAX_EXTRACTION_SIZE: 1 GB
SESSION_TIMEOUT: 7 días (limpieza automática)
ALLOWED_EXTENSIONS: .xml, .json, .txt, .yml, .yaml, .csv

RATE LIMITING (futuro):
  - 100 requests por hora por IP
  - 10 generaciones simultáneas por usuario
"""

# ============================================================================
# 6. SEGURIDAD
# ============================================================================

"""
CORS (Cross-Origin Resource Sharing):
  - Permitir localhost:3000 (frontend)
  - Permitir localhost:8000 (API)

VALIDACIÓN:
  - Validar tipo de archivo
  - Validar tamaño de archivo
  - Sanitizar nombres de archivo
  - Validar estructura de ZIP

ENCRIPTACIÓN:
  - Futuro: HTTPS en producción
  - Futuro: Archivos sensibles encriptados
"""

# ============================================================================
# 7. EJEMPLOS DE USO
# ============================================================================

"""
CURL:
------
# 1. Generar
curl -X POST "http://localhost:8000/generate/" \
  -F "file=@bot.zip"

# 2. Descargar
curl -O "http://localhost:8000/download/20240415_143022_123456/sdd"

Python:
-------
import requests

# 1. Generar
response = requests.post(
    'http://localhost:8000/generate/',
    files={'file': open('bot.zip', 'rb')}
)
session_id = response.json()['session_id']

# 2. Descargar
response = requests.get(
    f'http://localhost:8000/download/{session_id}/sdd'
)
with open('SDD.md', 'wb') as f:
    f.write(response.content)

JavaScript/Frontend:
--------------------
const response = await fetch('http://localhost:8000/generate/', {
  method: 'POST',
  body: new FormData(formElement)
});
const result = await response.json();
"""

# ============================================================================
# 8. MEJORAS FUTURAS
# ============================================================================

"""
CORTO PLAZO:
  - [ ] Autenticación con JWT
  - [ ] Caché de resultados
  - [ ] Rate limiting
  - [ ] Tests completos

MEDIANO PLAZO:
  - [ ] Exportación a PDF
  - [ ] Interfaz web (Next.js)
  - [ ] Base de datos (PostgreSQL)
  - [ ] Versionado de documentos

LARGO PLAZO:
  - [ ] Machine Learning para análisis
  - [ ] Generación de código
  - [ ] Integración con Git/Azure DevOps
  - [ ] Dashboard en tiempo real
"""
