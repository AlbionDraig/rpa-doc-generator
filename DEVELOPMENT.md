# Development Guide

Guia tecnica interna de RPA Doc Generator.
Para instalacion, ejecucion y uso de la API ver [README.md](README.md).

---

## Arquitectura de modulos

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

Orquesta el pipeline en cada endpoint:
1. `save_file` → `extract_project` → `parse_project`
2. `build_flow` + `build_tree`
3. `generate_flow_svg` + `convert_svg_to_png`
4. `generate_sdd_file` + `generate_sdd_word` + `generate_sdd_pdf`

Configuracion de runtime via `.env`:
- host/puerto (`APP_HOST`, `APP_PORT`)
- CORS (`CORS_ORIGINS`)
- paths (`OUTPUT_DIR`, `TMP_DIR`, `STATIC_DIR`)
- metadatos de API (`APP_TITLE`, `APP_VERSION`, `APP_DESCRIPTION`)

---

## Pipeline tecnico detallado

```
save_file(UploadFile)
    └── extract_project(zip_path)         # extrae en tmp/, valida path traversal
        └── parse_project(project_path)   # retorna project_data dict
            ├── build_flow(tasks)          # nodos/aristas del grafo
            ├── build_tree(project_path)   # arbol texto filtrado
            ├── generate_flow_svg(flow)    # SVG autocontenido
            ├── convert_svg_to_png(...)    # PNG intermedio para DOCX/PDF
            ├── generate_sdd_file(...)     # SDD_*.md
            ├── generate_sdd_word(...)     # SDD_*.docx
            └── generate_sdd_pdf(...)      # SDD_*.pdf
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
| `tests/test_aa360_pipeline.py` | Integracion | Pipeline completo parseo → flujo → SVG → SDD; seguridad ZIP |
| `tests/test_parser_quality_coverage.py` | Unitario | Helpers de `project_parser` y funciones de `sdd_generator` |
| `tests/test_extractor_coverage.py` | Unitario | Ramas de error de `extractor.extract_project` y `_validate_member_path` |
| `tests/test_task_ai_describer.py` | Unitario | Prompts/contexto AA360, fallback IA, priorizacion y secciones IA en reportes |

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

Cobertura de referencia (abril 2026):

| Modulo | Cobertura |
|--------|-----------|
| `app/parser/project_parser.py` | 85% |
| `app/generator/sdd_generator.py` | 90% |
| `app/ingestion/extractor.py` | 91% |
| `app/analysis/flow_builder.py` | 89% |
| `app/generator/diagram_generator.py` | 84% |
| **Total** | **89%** |

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
| Nuevo formato de exportacion | Nuevo archivo en `app/generator/` + endpoint en `main.py` |
| Nuevo tipo de descarga | `file_map` en `main.download_file` |
