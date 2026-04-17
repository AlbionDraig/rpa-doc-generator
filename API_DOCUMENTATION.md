# API Documentation - RPA Doc Generator

Documentacion tecnica alineada con el codigo actual del proyecto.

## Tabla de Contenido

1. [Endpoints HTTP](#1-endpoints-http)
2. [Contratos de Respuesta](#2-contratos-de-respuesta)
3. [Casos de Uso (Application Layer)](#3-casos-de-uso-application-layer)
4. [Pipeline de Generacion](#4-pipeline-de-generacion)
5. [Modelos de Datos Principales](#5-modelos-de-datos-principales)
6. [Configuracion (AppSettings)](#6-configuracion-appsettings)
7. [Limites, Rate Limit y Observabilidad](#7-limites-rate-limit-y-observabilidad)
8. [Templates y Salidas](#8-templates-y-salidas)
9. [Errores y Codigos](#9-errores-y-codigos)
10. [Licencia](#10-licencia)

---

## 1) Endpoints HTTP

Rutas definidas en los routers de FastAPI y registradas en la aplicacion.

### POST /generate/
- Archivo: app/api/routes/generate.py
- Handler: generate(file: UploadFile, request: Request)
- Caso de uso: run_generate_sdd(file, settings, logger)
- Response model: ArtifactGenerationResponse
- Errores documentados por ruta:
  - 400 Error de validacion
  - 429 Rate limit excedido
  - 404 Archivo no encontrado
  - 503 Capacidad temporal agotada
  - 500 Error interno

### POST /quality/
- Archivo: app/api/routes/quality.py
- Handler: quality(file: UploadFile, request: Request)
- Caso de uso: run_generate_quality(file, settings, logger)
- Response model: ArtifactGenerationResponse
- Errores documentados por ruta:
  - 400 Error de validacion
  - 429 Rate limit excedido
  - 404 Archivo no encontrado
  - 503 Capacidad temporal agotada
  - 500 Error interno

### GET /download/{session_id}/{file_type}
- Archivo: app/api/routes/download.py
- Handler: download_file(session_id: str, file_type: str, request: Request)
- Caso de uso: resolve_download_file(output_dir: Path, file_type: str)
- Retorno: FileResponse (application/octet-stream)
- Errores documentados por ruta:
  - 400 Tipo de archivo invalido
  - 404 Archivo no encontrado
  - 500 Error interno

Valores validos de file_type:
- sdd
- sdd_word
- sdd_pdf
- calidad
- calidad_word
- calidad_pdf
- flujo_svg

### GET /health
- Archivo: app/api/routes/system.py
- Handler: health(request: Request)
- Response model: HealthResponse

### GET /
- Archivo: app/api/routes/system.py
- Handler: root(request: Request)
- Response model: RootResponse

### Endpoints tecnicos de documentacion
Definidos en app/main.py:
- GET /docs
- GET /docs/oauth2-redirect
- GET /redoc
- GET /favicon.ico

---

## 2) Contratos de Respuesta

Modelos en app/api/contracts.py.

### RootResponse
```json
{
  "message": "RPA Doc Generator API",
  "version": "1.0.0",
  "docs": "http://localhost:8000/docs",
  "redoc": "http://localhost:8000/redoc",
  "health": "http://localhost:8000/health"
}
```

### HealthResponse
```json
{
  "status": "healthy",
  "app": "RPA Doc Generator",
  "version": "1.0.0",
  "timestamp": "2026-04-17T10:11:12.123456"
}
```

### ArtifactGenerationResponse
```json
{
  "status": "success",
  "session_id": "20260417_101112_123456",
  "proyecto": "PruebaTecnicaA360",
  "archivos_salida": {
    "sdd_path": "output/.../SDD_PruebaTecnicaA360.md",
    "sdd_word_path": "output/.../SDD_PruebaTecnicaA360.docx",
    "sdd_pdf_path": "output/.../SDD_PruebaTecnicaA360.pdf",
    "flujo_svg_path": "output/.../flujo_taskbots.svg"
  },
  "output_directory": "output/20260417_101112_123456"
}
```

Nota: en calidad los campos dentro de archivos_salida son:
- calidad_path
- calidad_word_path
- calidad_pdf_path

### ApiErrorResponse
```json
{
  "error": "Mensaje de error",
  "code": "error_code"
}
```

---

## 3) Casos de Uso (Application Layer)

Ubicacion: app/application/use_cases/

### run_generate_sdd(file, settings, logger)
Archivo: generate_sdd.py

Responsabilidad:
1. Guardar ZIP
2. Extraer proyecto
3. Parsear estructura AA360
4. Construir flujo
5. Construir arbol
6. Generar SVG + PNG del flujo
7. Generar SDD en MD, DOCX, PDF
8. Limpiar temporales

Retorna ArtifactGenerationResponse (diccionario serializable).

### run_generate_quality(file, settings, logger)
Archivo: generate_quality.py

Responsabilidad:
1. Guardar ZIP
2. Extraer proyecto
3. Parsear estructura
4. Generar reporte de calidad en MD
5. Exportar DOCX y PDF
6. Limpiar temporales

Retorna ArtifactGenerationResponse (diccionario serializable).

### resolve_download_file(output_dir: Path, file_type: str)
Archivo: download_artifact.py

Mapa real de tipos:
- sdd -> SDD_*.md
- sdd_word -> SDD_*.docx
- sdd_pdf -> SDD_*.pdf
- calidad -> Calidad_*.md
- calidad_word -> Calidad_*.docx
- calidad_pdf -> Calidad_*.pdf
- flujo_svg -> flujo_taskbots.svg

Si el tipo no existe retorna None.

---

## 4) Pipeline de Generacion

Pipeline principal de SDD:

1. Router POST /generate/
2. Control de concurrencia (generation_limiter.slot())
3. run_generate_sdd
4. save_file
5. extract_project
6. parse_project
7. build_flow + build_tree
8. generate_flow_svg + convert_svg_to_png
9. generate_sdd + generate_sdd_file
10. generate_sdd_word
11. generate_sdd_pdf
12. respuesta con rutas de artefactos

Pipeline principal de calidad:

1. Router POST /quality/
2. Control de concurrencia
3. run_generate_quality
4. save_file
5. extract_project
6. parse_project
7. generate_quality_file
8. generate_quality_word
9. generate_quality_pdf
10. respuesta con rutas de artefactos

---

## 5) Modelos de Datos Principales

### parse_project(path) -> dict
Archivo: app/parser/project_parser.py

Estructura principal:
```python
{
  "name": str,
  "path": str,
  "tasks": list[dict],
  "task_count": int,
  "metadata": {
    "description": str,
    "manifest": dict,
    "entrypoints": list[str],
  },
  "files": {
    "xml_count": int,
    "json_count": int,
    "taskbot_count": int,
    "manifest_count": int,
    "other_count": int,
  },
  "packages": list[dict],
  "systems": list[dict],
  "credentials": list[dict],
}
```

### task (elemento en tasks)
Construido en app/parser/_project_support.py::parse_taskbot

Campos relevantes:
- name
- path
- type (taskbot)
- role (main | subtask | taskbot)
- size
- description
- developer
- declared_date
- variables {input, output, internal}
- packages
- properties
- triggers
- dependencies
- task_calls
- actions
- node_stats
- error_handling
- systems
- credentials
- comments
- is_entrypoint (agregado luego por mark_entrypoints)

### flow (build_flow)
Archivo: app/analysis/flow_builder.py

```python
{
  "nodes": [
    {
      "id": str,
      "name": str,
      "path": str,
      "role": str,
      "is_entrypoint": bool,
      "type": str,
      "order": int,
      "node_count": int,
    }
  ],
  "edges": [
    {
      "from": str,
      "to": str,
      "label": str,
      "inputs_count": int,
      "outputs_count": int,
    }
  ],
  "summary": {
    "total_nodes": int,
    "total_edges": int,
    "entrypoints": list[str],
    "has_dependencies": bool,
  }
}
```

---

## 6) Configuracion (AppSettings)

Definida en app/application/settings.py.

### Campos del dataclass
- app_title: str
- app_version: str
- app_description: str
- app_host: str
- app_port: int
- app_log_level: str
- app_access_log: bool
- output_dir: Path
- tmp_dir: Path
- static_dir: Path
- cors_origins: list[str]
- public_base_url: str
- upload_chunk_size: int
- max_file_size: int
- max_extraction_size: int
- ai_quality_enabled: bool
- ai_timeout_seconds: int
- groq_api_key: str
- groq_model: str
- groq_base_url: str
- openai_api_key: str
- openai_model: str
- openai_base_url: str
- api_rate_limit_enabled: bool
- api_rate_limit_max_requests: int
- api_rate_limit_window_seconds: int
- max_concurrent_generations: int
- generation_acquire_timeout_seconds: int

### Variables de entorno soportadas
- APP_TITLE
- APP_VERSION
- APP_DESCRIPTION
- APP_HOST
- APP_PORT
- APP_LOG_LEVEL
- APP_ACCESS_LOG
- OUTPUT_DIR
- TMP_DIR
- STATIC_DIR
- CORS_ORIGINS
- PUBLIC_BASE_URL
- UPLOAD_CHUNK_SIZE
- MAX_FILE_SIZE
- MAX_EXTRACTION_SIZE
- AI_QUALITY_ENABLED
- AI_TIMEOUT_SECONDS
- GROQ_API_KEY
- GROQ_MODEL
- GROQ_BASE_URL
- OPENAI_API_KEY
- OPENAI_MODEL
- OPENAI_BASE_URL
- API_RATE_LIMIT_ENABLED
- API_RATE_LIMIT_MAX_REQUESTS
- API_RATE_LIMIT_WINDOW_SECONDS
- MAX_CONCURRENT_GENERATIONS
- GENERATION_ACQUIRE_TIMEOUT_SECONDS

---

## 7) Limites, Rate Limit y Observabilidad

### Concurrencia de generacion
- Implementacion: ConcurrencyLimiter (app/limits.py)
- Integracion: app.state.generation_limiter en create_app()
- Uso en rutas: async with generation_limiter.slot()
- Si no adquiere slot: HTTP 503 con code capacity_exceeded

### Rate limiting por endpoint
- Middleware: EndpointRateLimitMiddleware (app/limits.py)
- Protege rutas: /generate/ y /quality/
- Configurable por settings:
  - api_rate_limit_enabled
  - api_rate_limit_max_requests
  - api_rate_limit_window_seconds
- Exceso devuelve HTTP 429

### Observabilidad
- Middleware: ObservabilityMiddleware (app/observability.py)
- Funciones auxiliares usadas por casos de uso:
  - bind_session
  - bind_logger
  - reset_session

---

## 8) Templates y Salidas

### Templates
Ubicacion: app/templates/
- sdd_template.md
- quality_template.md
- pdf_style.css
- word_theme.json

### Directorios de salida
- output/: artefactos finales por session_id
- tmp/: archivos cargados y extracciones temporales

### Archivos generados (SDD)
- SDD_<Proyecto>.md
- SDD_<Proyecto>.docx
- SDD_<Proyecto>.pdf
- flujo_taskbots.svg

### Archivos generados (Calidad)
- Calidad_<Proyecto>.md
- Calidad_<Proyecto>.docx
- Calidad_<Proyecto>.pdf

---

## 9) Errores y Codigos

El formato de error HTTP estandar es:
```json
{"error": "...", "code": "..."}
```

Codigos internos mas relevantes observables en rutas:
- invalid_file_type (download, 400)
- not_found (download, 404)
- internal_error (download, 500)
- capacity_exceeded (generate/quality, 503)

Adicionalmente, map_exception_to_http() en rutas generate/quality transforma errores de dominio a HTTPException.

---

## 10) Licencia

Este proyecto se distribuye bajo licencia MIT.
Su uso y distribucion se realizan con autorizacion del titular del repositorio.

Texto completo: [LICENSE](LICENSE)

---

Documento actualizado para reflejar el estado actual del codigo en la rama master.
