# Development Guide

Guia tecnica interna de RPA Doc Generator.
Para instalacion, ejecucion y uso de la API ver [README.md](README.md).

---

## Arquitectura de modulos

La aplicacion sigue un monolito modular con separacion por capas:

- `app/main.py` actua como bootstrap (configuracion global, middleware, mount de static y routers).
- `app/api/` define contratos HTTP (endpoints, validacion y mapeo de errores HTTP).
- `app/application/` concentra orquestacion de casos de uso y settings de runtime.
- `app/ingestion`, `app/parser`, `app/analysis`, `app/generator` mantienen las capacidades tecnicas del dominio AA360.

### `app/api/`

- `routes/generate.py` — endpoint `POST /generate/`; delega la orquestacion al caso de uso `run_generate_sdd`.
- `routes/quality.py` — endpoint `POST /quality/`; delega a `run_generate_quality`.
- `routes/download.py` — endpoint `GET /download/{session_id}/{file_type}`; delega resolucion de artefacto.
- `routes/system.py` — endpoints `GET /` y `GET /health`.
- `deps.py` — acceso centralizado a `settings` y `logger` via `request.app.state`.

### `app/application/`

- `settings.py` — modelo `AppSettings` para cargar variables de entorno y evitar dispersion de configuracion.
- `use_cases/generate_sdd.py` — pipeline SDD (ingestion, parseo, flujo, arbol, SVG, Markdown, DOCX, PDF).
- `use_cases/generate_quality.py` — pipeline de reporte de calidad (Markdown, DOCX, PDF).
- `use_cases/download_artifact.py` — mapeo de `file_type` a artefacto descargable.

### `app/ingestion/`

- `uploader.py` — Recibe el `UploadFile` de FastAPI, valida extension `.zip`, controla tamano maximo (`MAX_FILE_SIZE`) y lo guarda en `TMP_DIR`.
- `extractor.py` — Descomprime el ZIP de forma segura (previene path traversal) y controla tamano total extraido (`MAX_EXTRACTION_SIZE`). Retorna la ruta de la carpeta extraida.

### `app/parser/`

- `project_parser.py` — Punto de entrada: `parse_project(path)`.
  - Carga `manifest.json` para descubrir taskbots por `contentType`.
  - Fallback: escanea el directorio buscando JSONs con las claves `nodes`, `variables`, `packages`, `properties`.
  - Extrae por taskbot: variables input/output/internas, nodos AA360, llamadas `runTask`, credenciales, sistemas externos, comentarios de cabecera (developer, fecha, descripcion).
  - Retorna un dict estructurado con `tasks`, `packages`, `systems`, `credentials`, `metadata`, `files`.

### `app/analysis/`

- `flow_builder.py` — Construye nodos y aristas a partir de las dependencias `scannedDependencies` del manifest y de las llamadas `runTask` detectadas. Retorna `{nodes, edges, summary}`.
- `tree_builder.py` — Genera un arbol de directorios como texto, filtrando carpetas `metadata`, archivos `.jar`, imagenes, cache y archivos ocultos.
- `task_ai_describer.py` — Capa de analisis IA (Groq/OpenAI-compatible + fallback heuristico): interpretacion por taskbot, priorizacion de hallazgos, plan de remediacion, insights SDD.

### `app/generator/`

- `sdd_generator.py` — Rellena `sdd_template.md` con las secciones del SDD. Tambien contiene `generate_quality_file` que produce el reporte de observaciones de calidad.
- `diagram_generator.py` — Genera el SVG autocontenido del flujo con layout automatico por niveles (BFS desde entrypoints). Tambien convierte el SVG a PNG via `svglib`+`reportlab` para embeber en DOCX/PDF.
- `word_generator.py` — Exporta SDD y Calidad a `.docx` via `python-docx`.
- `pdf_generator.py` — Exporta SDD y Calidad a `.pdf` via `reportlab`.

### `app/main.py`

Bootstrap de aplicacion:
1. Carga env y construye `AppSettings`.
2. Configura FastAPI, CORS y rutas de docs.
3. Registra `settings`/`logger` en `app.state`.
4. Incluye routers de `app/api/routes`.

Configuracion de runtime via `.env`:
- host/puerto (`APP_HOST`, `APP_PORT`)
- CORS (`CORS_ORIGINS`)
- paths (`OUTPUT_DIR`, `TMP_DIR`, `STATIC_DIR`)
- metadatos de API (`APP_TITLE`, `APP_VERSION`, `APP_DESCRIPTION`)

---

## Pipeline tecnico detallado

```
HTTP Router (`app/api/routes/*.py`)
  └── Use Case (`app/application/use_cases/*.py`)
    ├── save_file(UploadFile)
    ├── extract_project(zip_path)         # extrae en tmp/, valida path traversal
    ├── parse_project(project_path)       # retorna project_data dict
    ├── build_flow(tasks) / build_tree(project_path)
    ├── generate_flow_svg(flow) / convert_svg_to_png(...)
    ├── generate_sdd_file(...) / generate_quality_file(...)
    ├── generate_*_word(...)
    └── generate_*_pdf(...)
```

---

## Tests

### Requisitos previos

Instalar las dependencias de desarrollo en el virtual environment:

```bash
pip install pytest coverage
```

---

### Archivos de tests

| Archivo | Tipo | Cobertura principal |
|---------|------|---------------------|
| `tests/test_api_structure.py` | Unitario/API smoke | Estabilidad de endpoints principales y wiring de routers |
| `tests/test_routes_error_mapping.py` | Unitario/API | Mapeo de errores HTTP (400/404/500) y rutas sistema/download |
| `tests/test_use_cases_coverage.py` | Unitario/Application | Orquestacion de casos de uso SDD/Calidad y resolucion de artefactos |
| `tests/test_uploader_tree_settings_coverage.py` | Unitario | Guardado de ZIP, arbol de directorios y parsing de settings/env |
| `tests/test_export_generators_coverage.py` | Unitario/Export | Generacion DOCX/PDF, helpers de exportacion y observaciones de calidad |
| `tests/test_flow_ai_edge_coverage.py` | Unitario/Analysis | Ramas de flujo (ciclos/dedupe) y ramas AI/fallback/normalizacion |
| `tests/test_diagram_main_coverage.py` | Unitario/API+Diagram | Helpers de diagrama SVG/PNG, docs/redoc y bootstrap de app |
| `tests/test_parser_additional_coverage.py` | Unitario/Parser | Ramas internas adicionales del parser (discovery, helpers, parse fallbacks) |
| `tests/test_aa360_pipeline.py` | Integracion | Pipeline completo parseo → flujo → SVG → SDD; seguridad ZIP |
| `tests/test_parser_quality_coverage.py` | Unitario | Helpers de `project_parser` y funciones de `sdd_generator` |
| `tests/test_extractor_coverage.py` | Unitario | Ramas de error de `extractor.extract_project` y `_validate_member_path` |
| `tests/test_task_ai_describer.py` | Unitario | Prompts/contexto AA360, fallback IA, priorizacion y secciones IA en reportes |

**`test_api_structure.py`**
- `test_system_endpoints_are_available` — valida `GET /` y `GET /health`.
- `test_required_upload_endpoints_exist` — valida presencia de `POST /generate/` y `POST /quality/`.
- `test_download_route_exists` — valida presencia de `GET /download/{session_id}/{file_type}`.

**`test_routes_error_mapping.py`**
- valida mapeo de excepciones en `generate` y `quality` a codigos HTTP `400/404/500`.
- valida ramas de `download` (tipo invalido, archivo ausente, excepcion inesperada y exito).
- valida payload de `GET /` y `GET /health`.

**`test_use_cases_coverage.py`**
- valida flujo exitoso de `run_generate_sdd`, incluyendo eliminacion del PNG intermedio.
- valida flujo exitoso de `run_generate_quality`, incluyendo lectura del markdown generado para PDF.
- valida resolucion de artefactos en `download_artifact`.

**`test_uploader_tree_settings_coverage.py`**
- valida `save_file` para extension invalida, archivo vacio, limite de tamano y ruta exitosa.
- valida `build_tree`, `should_exclude`, `_detect_file_kind` y `_format_size`.
- valida parsing de `AppSettings` y fallback de `_env_int`.

**`test_export_generators_coverage.py`**
- valida `generate_sdd_word` y `generate_quality_word` con fixtures reales de proyecto AA360.
- valida helpers de Word (`_format_size`, `_describe_error_handling`, `_unique_preserve`, `_collect_quality_observations`).
- valida helpers PDF (`_sanitize_tree_for_pdf`, `_fix_pre_newlines`, `_fix_heading_anchors`, `_escape_html`).
- valida `generate_sdd_pdf` y `generate_quality_pdf` con `pisa.CreatePDF` mockeado y rutas de error.

**`test_flow_ai_edge_coverage.py`**
- cubre ramas de `flow_builder`: lista vacia, deduplicacion de aristas, dependencias desconocidas y fallback por ciclo.
- cubre ramas de `task_ai_describer`: parseo JSON, normalizadores, fallback por provider/URL, caminos AI en SDD/priorizacion.
- cubre helpers heuristicas (`_safe_timeout`, severidades, extraccion de task name, top tasks).

**`test_diagram_main_coverage.py`**
- cubre helpers de `diagram_generator` (`_blend_color`, `_wrap_text`, `_build_edge_label`, `_empty_svg`).
- cubre `generate_flow_svg` (flujo vacio y flujo con nodos/aristas).
- cubre `convert_svg_to_png` en ramas de exito, parseo nulo y excepcion.
- cubre endpoints de docs/redoc y ejecucion de `create_app` en `main`.

**`test_parser_additional_coverage.py`**
- cubre ramas extra del parser: manifest invalido, discovery fallback por estructura taskbot.
- cubre helpers de parse y sanitizacion (`_summarize_node`, `_extract_task_call`, `_flatten_attribute_values`, `_extract_systems_from_node`, `_extract_credential_from_node`).
- cubre rutas de error en parse XML/JSON y excepciones controladas en extractores auxiliares.

**`test_aa360_pipeline.py`**
- `test_parse_project_and_flow_use_real_taskbot_dependencies` — ejecuta el pipeline de extremo a extremo
  con un proyecto sintetico de 2 taskbots (Main → Lookup) y verifica orden, entrypoints, aristas,
  SVG, SDD y contrato de variables.
- `test_extract_project_rejects_zip_traversal` — confirma que un ZIP con entrada `../escape.txt`
  es rechazado con `ValueError` antes de escribir nada en disco.

**`test_parser_quality_coverage.py`**
- `test_sanitize_text_masks_sensitive_data` — passwords, URLs con credenciales, rutas Windows, JDBC, file://.
- `test_analyze_nodes_extracts_stats_calls_systems_and_credentials` — arbol de nodos AA360 con If, Loop,
  try/catch/finally, runTask, Browser, Database y CredentialVault.
- `test_dependency_entrypoints_and_collections` — deduplicacion de dependencias, marcado de entrypoints
  y recopilacion de paquetes, sistemas y credenciales a nivel proyecto.
- `test_parse_project_and_file_summary_without_manifest` — deteccion de taskbots por estructura JSON
  cuando no hay `manifest.json`, conteo de archivos auxiliares, excluye `metadata/` y `.jar`.
- `test_sdd_quality_and_file_generation` — observaciones de calidad (nodos deshabilitados, try sin catch,
  ruta hardcodeada, DB sin vault), generacion del SDD y escritura de ambos archivos en disco.

**`test_extractor_coverage.py`**
- `test_extract_project_raises_file_not_found` — ruta al ZIP inexistente.
- `test_extract_project_raises_bad_zip_when_testzip_detects_corruption` — mock de `testzip` que reporta corrupcion.
- `test_extract_project_re_raises_unexpected_exception` — excepciones inesperadas no se absorben.
- `test_extract_project_raises_bad_zip_for_invalid_archive_file` — archivo de texto pasado como ZIP.
- `test_validate_member_path_allows_safe_relative_paths` — ruta relativa dentro del destino: OK.
- `test_validate_member_path_rejects_path_traversal` — `../escape.txt` fuera del destino: ValueError.

**`test_task_ai_describer.py`**
- valida interpretacion IA por taskbot con fallback heuristico.
- valida priorizacion de hallazgos y plan por sprint con criterios de cierre.
- valida prompts especializados en Automation Anywhere 360 (taskbots, runTask, Credential Vault, triggers).

---

### Ejecutar los tests

```bash
# Todos los tests (modo silencioso)
python -m pytest -q

# Con salida detallada
python -m pytest -v

# Un archivo especifico
python -m pytest tests/test_aa360_pipeline.py -v

# Un test especifico
python -m pytest tests/test_extractor_coverage.py::ExtractorCoverageTests::test_extract_project_raises_file_not_found -v

# Detener al primer fallo
python -m pytest -x
```

---

### Medir cobertura

```bash
# Ejecutar con recoleccion de cobertura
python -m coverage run -m pytest tests/ -q

# Reporte en consola (muestra lineas no cubiertas)
python -m coverage report -m

# Reporte HTML interactivo (abre htmlcov/index.html en el navegador)
python -m coverage html
```

Cobertura de referencia (abril 2026, despues de ampliar tests de API/Application/Export/Analysis/Parser):

| Modulo | Cobertura |
|--------|-----------|
| `app/api/routes/generate.py` | 100% |
| `app/api/routes/quality.py` | 100% |
| `app/api/routes/download.py` | 100% |
| `app/api/routes/system.py` | 100% |
| `app/application/use_cases/generate_sdd.py` | 100% |
| `app/application/use_cases/generate_quality.py` | 100% |
| `app/application/use_cases/download_artifact.py` | 100% |
| `app/ingestion/uploader.py` | 100% |
| `app/analysis/flow_builder.py` | 100% |
| `app/analysis/task_ai_describer.py` | 95% |
| `app/analysis/tree_builder.py` | 97% |
| `app/main.py` | 98% |
| `app/generator/pdf_generator.py` | 99% |
| `app/generator/diagram_generator.py` | 99% |
| `app/generator/word_generator.py` | 94% |
| `app/parser/project_parser.py` | 91% |
| `app/generator/sdd_generator.py` | 91% |
| `app/ingestion/extractor.py` | 92% |
| **Total** | **95%** |

---

## Convenciones

- Propagar errores de validacion con `ValueError` y mensaje claro; FastAPI los captura como `400`.
- No loguear valores de credenciales, tokens ni rutas de usuario.
- Nombres de secciones y campos en los documentos generados en espanol (consistencia con clientes).
- Mantener funciones de generacion puras: reciben dicts, retornan strings.

---

## Puntos de extension

| Que agregar | Donde |
|-------------|-------|
| Nueva heuristica de calidad | `sdd_generator._generate_quality_observations` |
| Nuevo detector de sistemas externos | `project_parser._extract_systems_from_node` |
| Nuevo detector de credenciales | `project_parser._extract_credential_from_node` |
| Nuevo formato de exportacion | Nuevo adapter en `app/generator/` + use case en `app/application/use_cases/` + endpoint en `app/api/routes/` |
| Nuevo tipo de descarga | Resolver en `app/application/use_cases/download_artifact.py` |
