# Development Guide

Guia tecnica interna de RPA Doc Generator.

Para uso general de la API:
- README.md

Para contratos y modelos exactos del codigo:
- API_DOCUMENTATION.md

## Tabla de contenido

1. [Arquitectura](#arquitectura)
2. [Endpoints Reales](#endpoints-reales)
3. [Capa API](#capa-api)
4. [Capa Application](#capa-application)
5. [Capa Ingestion](#capa-ingestion)
6. [Capa Parser](#capa-parser)
7. [Capa Analysis](#capa-analysis)
8. [Capa Generator](#capa-generator)
9. [Middleware y Operacion](#middleware-y-operacion)
10. [Templates](#templates)
11. [Convenciones de Desarrollo](#convenciones-de-desarrollo)
12. [Pruebas](#pruebas)
13. [Licencia](#licencia)

---

## Arquitectura

La aplicacion sigue un monolito modular por capas:

- app/main.py
  - Bootstrap de FastAPI
  - Registro de middlewares
  - Montaje de static
  - Inclusion de routers
- app/api/
  - Endpoints HTTP y contratos de respuesta
- app/application/
  - AppSettings y casos de uso
- app/ingestion/
  - Carga y extraccion segura de ZIP
- app/parser/
  - Parseo de proyectos AA360
- app/analysis/
  - Flujo, arbol e insights de calidad
- app/generator/
  - Exportadores MD, DOCX, PDF y SVG

---

## Endpoints Reales

Definidos por routers:

- POST /generate/
- POST /quality/
- GET /download/{session_id}/{file_type}
- GET /health
- GET /

Definidos en app/main.py (tecnicos/docs):

- GET /docs
- GET /docs/oauth2-redirect
- GET /redoc
- GET /favicon.ico

---

## Capa API

### app/api/routes/generate.py
- Handler: generate(file, request)
- Invoca: run_generate_sdd(file, settings, logger)
- Controla concurrencia con generation_limiter.slot()
- Mapea errores via map_exception_to_http()

### app/api/routes/quality.py
- Handler: quality(file, request)
- Invoca: run_generate_quality(file, settings, logger)
- Misma estrategia de concurrencia y mapeo de errores

### app/api/routes/download.py
- Handler: download_file(session_id, file_type, request)
- Resuelve archivo con resolve_download_file(output_dir, file_type)
- Retorna FileResponse

### app/api/routes/system.py
- Handler health(): retorna estado de aplicacion
- Handler root(): retorna enlaces a docs/redoc/health

### app/api/contracts.py
Modelos Pydantic:
- RootResponse
- HealthResponse
- ArtifactGenerationResponse
- ApiErrorResponse

---

## Capa Application

### app/application/settings.py
Dataclass AppSettings construido desde entorno (from_env).

Campos clave:
- app_title, app_version, app_description
- app_host, app_port, app_log_level, app_access_log
- output_dir, tmp_dir, static_dir
- cors_origins, public_base_url
- upload_chunk_size, max_file_size, max_extraction_size
- ai_quality_enabled, ai_timeout_seconds
- groq_api_key, groq_model, groq_base_url
- openai_api_key, openai_model, openai_base_url
- api_rate_limit_enabled, api_rate_limit_max_requests, api_rate_limit_window_seconds
- max_concurrent_generations, generation_acquire_timeout_seconds

### app/application/use_cases/generate_sdd.py
Funcion publica:
- run_generate_sdd(file, settings, logger)

Pipeline:
1. save_file
2. extract_project
3. parse_project
4. build_flow
5. build_tree
6. generate_flow_svg + convert_svg_to_png
7. generate_sdd / generate_sdd_file
8. generate_sdd_word / generate_sdd_pdf
9. limpieza de temporales

### app/application/use_cases/generate_quality.py
Funcion publica:
- run_generate_quality(file, settings, logger)

Pipeline:
1. save_file
2. extract_project
3. parse_project
4. generate_quality_file
5. generate_quality_word
6. generate_quality_pdf
7. limpieza de temporales

### app/application/use_cases/download_artifact.py
Funcion publica:
- resolve_download_file(output_dir, file_type)

Tipos soportados:
- sdd
- sdd_word
- sdd_pdf
- calidad
- calidad_word
- calidad_pdf
- flujo_svg

---

## Capa Ingestion

### app/ingestion/uploader.py
- save_file(file, settings=None)
- Valida extension .zip
- Escribe en chunks
- Aplica limite max_file_size

### app/ingestion/extractor.py
- extract_project(zip_path, settings=None)
- Verifica integridad del ZIP
- Previene path traversal
- Aplica limite max_extraction_size

---

## Capa Parser

Punto de entrada:
- app/parser/project_parser.py -> parse_project(path)

Submodulos:
- _common.py: sanitizacion, helpers de lectura y normalizacion
- _documents.py: parseo XML/JSON auxiliar
- _node_analysis.py: analisis de nodos, stats, systems, credentials, task_calls
- _project_support.py: discovery, dependencias, entrypoints, agregaciones de proyecto

Salida principal de parse_project:
- name, path
- tasks, task_count
- metadata (description, manifest, entrypoints)
- files (xml_count, json_count, taskbot_count, manifest_count, other_count)
- packages, systems, credentials

---

## Capa Analysis

### app/analysis/flow_builder.py
- build_flow(tasks)
- Retorna:
  - nodes con id, name, path, role, is_entrypoint, type, order, node_count
  - edges con from, to, label, inputs_count, outputs_count
  - summary con total_nodes, total_edges, entrypoints, has_dependencies

### app/analysis/tree_builder.py
- build_tree(path, prefix="", include_stats=True)
- Genera arbol de directorios para documentacion

### app/analysis/task_ai_describer.py
Funciones publicas:
- describe_task_with_ai(task, settings=None)
- build_quality_task_descriptions(tasks, settings=None)
- classify_task_for_aa360(task)
- build_sdd_ai_insights(project_data, flow=None, settings=None)
- build_quality_prioritization(project_data, task_descriptions, observations, settings=None)

---

## Capa Generator

### app/generator/sdd_generator.py
- generate_sdd(...)
- generate_sdd_file(...)
- generate_quality_file(...)

### app/generator/word_generator.py
- generate_sdd_word(...)
- generate_quality_word(...)

### app/generator/pdf_generator.py
- generate_sdd_pdf(...)
- generate_quality_pdf(...)

### app/generator/diagram_generator.py
- generate_flow_svg(flow)
- convert_svg_to_png(svg_path, png_path, scale=3.0)

---

## Middleware y Operacion

Configurados en app/main.py:

- ObservabilityMiddleware
- EndpointRateLimitMiddleware (protege /generate/ y /quality/)
- CORSMiddleware

Tambien se inicializa:
- ConcurrencyLimiter en app.state.generation_limiter

---

## Templates

Ubicacion: app/templates/

- sdd_template.md
- quality_template.md
- pdf_style.css
- word_theme.json

Uso:
- Los generadores intentan cargar template/estilo del archivo
- Si falta archivo, usan fallback interno

---

## Convenciones de Desarrollo

- Mantener errores HTTP en formato {"error", "code"}
- Evitar loguear secretos y credenciales
- Mantener textos de salida en espanol para consistencia de negocio
- Centralizar configuracion en AppSettings
- Preferir funciones de generacion puras cuando no dependen de IO

---

## Pruebas

Suite de tests en tests/ con cobertura sobre API, parser, analysis, generators, ingestion y use cases.

Comandos habituales:

```bash
python -m pytest -q
python -m coverage erase
python -m coverage run -m pytest tests -q
python -m coverage report -m
```

Para estado de cobertura y badges, revisar README.md.

---

## Licencia

Este proyecto se distribuye bajo licencia MIT.
Su uso y distribucion se realizan con autorizacion del titular del repositorio.

Texto completo: [LICENSE](LICENSE)
