# RPA Doc Generator

[![CI](https://github.com/AlbionDraig/rpa-doc-generator/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/AlbionDraig/rpa-doc-generator/actions/workflows/ci.yml)
![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)

Generador automatico de documentacion tecnica para bots de Automation Anywhere 360.

Recibe un ZIP exportado desde AA360 y produce documentacion SDD y reportes de calidad en Markdown, Word y PDF, mas un diagrama SVG del flujo entre taskbots.

---

## Que genera

### `POST /generate/` — Documentacion SDD

| Archivo | Descripcion |
|---------|-------------|
| `SDD_<Proyecto>.md` | Documento completo en Markdown |
| `SDD_<Proyecto>.docx` | Documento en Word |
| `SDD_<Proyecto>.pdf` | Documento en PDF |
| `flujo_taskbots.svg` | Diagrama SVG del flujo entre taskbots |

**Secciones del SDD generado:**

1. Informacion General (nombre, entrypoints, paquetes AA360, sistemas externos)
2. Resumen Ejecutivo con IA opcional (vision general del bot para devs)
3. Estadisticas (nodos, condiciones, bucles, llamadas runTask, errores)
4. Flujo Principal entre Taskbots (imagen SVG embebida)
5. Contrato de Dependencias (variables enviadas y recibidas en cada runTask)
6. Inventario de Taskbots (rol, ruta, descripcion, developer, acciones, paquetes)
7. Contrato de Variables (tablas input/output/internas por taskbot)
8. Credenciales y Vaults
9. Sistemas Externos y Configuracion Tecnica
10. Paquetes AA360 Detectados
11. Puntos Criticos del Bot con IA opcional
12. Estructura del Proyecto (arbol filtrado)

### `POST /quality/` — Reporte de Calidad

| Archivo | Descripcion |
|---------|-------------|
| `Calidad_<Proyecto>.md` | Reporte en Markdown |
| `Calidad_<Proyecto>.docx` | Reporte en Word |
| `Calidad_<Proyecto>.pdf` | Reporte en PDF |

**Que analiza el reporte de calidad:**

- Nodos deshabilitados (codigo muerto)
- Taskbots sin bloque try/catch
- Try sin catch correspondiente
- Taskbots sin descripcion declarada en cabecera
- Taskbots sin developer declarado
- Rutas de archivo hardcodeadas
- Conexiones a base de datos sin credenciales via CredentialVault

---

## Caracteristicas principales

- Parseo de `manifest.json` para descubrir taskbots y dependencias reales.
- Fallback de deteccion por estructura JSON cuando no hay manifest.
- Extraccion de metadatos de cabecera desde nodos `Comment` (developer, fecha, descripcion).
- Analisis de nodos AA360: condiciones, bucles, manejo de errores, invocaciones `runTask`.
- Inventario completo de variables input/output/internas con tipo, default y descripcion.
- Deteccion de credenciales via CredentialVault, sistemas externos (URLs, DB, archivos).
- Inventario de paquetes AA360 con version.
- Diagrama SVG de flujo con layout automatico entre taskbots.
- Arbol de directorios filtrado (excluye metadata, .jar, imagenes, cache).
- Sanitizacion de datos sensibles (credenciales, rutas de usuario).
- Exportacion a Markdown, DOCX y PDF.
- Interpretacion funcional por taskbot con IA opcional en el reporte de calidad.

---

## IA opcional para calidad por taskbot

El endpoint `POST /quality/` puede incluir una seccion por taskbot con:

- Que hace la tarea segun el analisis
- Funcion que cumple en el flujo
- Criticidad estimada
- Riesgos detectados
- Mejoras recomendadas
- Fuente (`ai` o `heuristic`) y confianza estimada

Adicionalmente genera:

- Priorizacion inteligente de hallazgos (bloqueante/alto/medio/bajo)
- Plan de remediacion por sprint (P1/P2/P3 con esfuerzo S/M/L)
- Criterio de cierre por accion (Definition of Done)

Si no se configura IA, el sistema usa fallback heuristico local (sin llamadas externas).

Para Groq se usa su endpoint compatible con OpenAI. Si defines `GROQ_API_KEY`, el proyecto prioriza Groq automaticamente.

Variables de entorno:

| Variable | Descripcion | Default |
|----------|-------------|---------|
| `APP_TITLE` | Titulo de la API | `RPA Doc Generator` |
| `APP_VERSION` | Version de la API | `1.0.0` |
| `APP_DESCRIPTION` | Descripcion de la API | `Generador automatico...` |
| `APP_HOST` | Host de arranque uvicorn | `0.0.0.0` |
| `APP_PORT` | Puerto de arranque uvicorn | `8000` |
| `APP_LOG_LEVEL` | Nivel de log uvicorn/app (`debug/info/warning/error`) | `info` |
| `APP_ACCESS_LOG` | Habilita access log de uvicorn | `true` |
| `PUBLIC_BASE_URL` | URL base publicada en endpoint `/` | `http://localhost:8000` |
| `CORS_ORIGINS` | Lista de origenes CORS separada por comas | `http://localhost,...` |
| `OUTPUT_DIR` | Directorio de salida de artefactos | `./output` |
| `TMP_DIR` | Directorio temporal para uploads y extraccion | `./tmp` |
| `STATIC_DIR` | Directorio de archivos estaticos | `./app/static` |
| `UPLOAD_CHUNK_SIZE` | Tamano de lectura por bloque al subir ZIP (bytes) | `1048576` |
| `MAX_FILE_SIZE` | Tamano maximo de ZIP recibido (bytes) | `524288000` |
| `MAX_EXTRACTION_SIZE` | Tamano maximo total descomprimido (bytes) | `1073741824` |
| `AI_QUALITY_ENABLED` | Habilita inferencia con IA (`true/false`) | `false` |
| `GROQ_API_KEY` | API key de Groq | - |
| `GROQ_MODEL` | Modelo Groq para la interpretacion | `llama-3.3-70b-versatile` |
| `GROQ_BASE_URL` | Base URL de Groq compatible con OpenAI | `https://api.groq.com/openai/v1` |
| `OPENAI_API_KEY` | API key para endpoint compatible con OpenAI | - |
| `OPENAI_MODEL` | Modelo de chat a utilizar | `gpt-4o-mini` |
| `OPENAI_BASE_URL` | Base URL del proveedor compatible (`.../v1`) | `https://api.openai.com/v1` |
| `AI_TIMEOUT_SECONDS` | Timeout por llamada de IA | `25` |
| `API_RATE_LIMIT_ENABLED` | Habilita rate limit para endpoints pesados | `true` |
| `API_RATE_LIMIT_MAX_REQUESTS` | Maximo de solicitudes por IP en ventana | `30` |
| `API_RATE_LIMIT_WINDOW_SECONDS` | Ventana de rate limit (segundos) | `60` |
| `MAX_CONCURRENT_GENERATIONS` | Generaciones simultaneas permitidas (`/generate`, `/quality`) | `2` |
| `GENERATION_ACQUIRE_TIMEOUT_SECONDS` | Timeout para esperar slot de concurrencia | `10` |

---

## Requisitos

- Python 3.8+
- pip

## Instalacion

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

## Ejecucion

```bash
# Windows
run.bat

# Linux/macOS
chmod +x run.sh && ./run.sh

# Manual
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API disponible en `http://localhost:8000`.
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Personalizacion mediante Templates

La generacion de documentos puede personalizarse sin recompilar el codigo modificando los templates en `app/templates/`:

| Archivo | Customiza | Ejemplo |
|---------|-----------|---------|
| `sdd_template.md` | Estructura y seccion del SDD Markdown | Reordenar secciones, cambiar encabezados |
| `quality_template.md` | Estructura del reporte de calidad Markdown | Agregar nuevas secciones de analisis |
| `pdf_style.css` | Estilos CSS para PDFs (colores, tipografia) | Cambiar colores corporativos, fuentes |
| `word_theme.json` | Tema de Word (colores RGB/HEX, espaciado) | Aplicar branding corporativo |

**Ventajas:**
- Cambios persisten entre despliegues
- Sin necesidad de modificar codigo Python
- Fallback automatico si el template no existe o es invalido
- Versionamiento en git

**Ejemplo: Cambiar colores corporativos en PDF y Word**

1. Editar `app/templates/pdf_style.css`:
   ```css
   h1 { border-bottom: 3px solid #YOUR_COLOR; }
   ```

2. Editar `app/templates/word_theme.json`:
   ```json
   "accent": {"rgb": [R, G, B], "hex": "RRGGBB"}
   ```

Los documentos generados usaran los nuevos colores sin reiniciar la aplicacion.

---

## Calidad y Cobertura

Baseline validado al 2026-04-17:

- Suite automatizada: `96` tests pasando
- Cobertura total de lineas: `98%`
- Cobertura destacada:
  - `app/generator/word_generator.py`: `96%`
  - `app/application/use_cases/generate_quality.py`: `100%`
  - `app/analysis/task_ai_describer.py`: `95%`

Comandos usados para validacion:

```bash
python -m coverage erase
python -m coverage run -m pytest tests -q
python -m coverage report -m
```

## CI/CD

El repositorio incluye workflow de GitHub Actions en [.github/workflows/ci.yml](.github/workflows/ci.yml).

Checks incluidos en cada push/PR a `master`:

- Lint critico (errores de sintaxis y referencias invalidas) con `ruff`
- Suite de tests con `pytest`
- Gate de cobertura con `coverage` (`--fail-under=90`)
- Auditoria de dependencias con `pip-audit` (no bloqueante por ahora)

Comandos equivalentes para ejecutar localmente:

```bash
pip install -r requirements.txt -r requirements-dev.txt
ruff check --select E9,F63,F7,F82 app tests
python -m coverage erase
python -m coverage run -m pytest tests -q
python -m coverage report --fail-under=90 -m
```

---

## API

### `GET /`

```json
{
  "message": "RPA Doc Generator API",
  "version": "1.0.0",
  "docs": "http://localhost:8000/docs",
  "redoc": "http://localhost:8000/redoc",
  "health": "http://localhost:8000/health"
}
```

---

### `GET /health`

```json
{
  "status": "healthy",
  "app": "RPA Doc Generator",
  "version": "1.0.0",
  "timestamp": "2026-04-16T10:22:33.123456"
}
```

---

### `POST /generate/`

Genera documentacion SDD completa.

**Request:** `multipart/form-data`, campo `file` (`.zip` exportado de AA360).

**Response `200`:**

```json
{
  "status": "success",
  "session_id": "20260416_102233_123456",
  "proyecto": "MiBot",
  "archivos_salida": {
    "sdd_path": "output/20260416_102233_123456/SDD_MiBot.md",
    "sdd_word_path": "output/20260416_102233_123456/SDD_MiBot.docx",
    "sdd_pdf_path": "output/20260416_102233_123456/SDD_MiBot.pdf",
    "flujo_svg_path": "output/20260416_102233_123456/flujo_taskbots.svg"
  },
  "output_directory": "output/20260416_102233_123456"
}
```

**Errores:** `400` validacion | `404` recurso no encontrado | `500` error interno

**Ejemplo:**

```bash
curl -X POST "http://localhost:8000/generate/" -F "file=@mi_bot.zip"
```

---

### `POST /quality/`

Genera reporte de observaciones de calidad.

**Request:** `multipart/form-data`, campo `file` (`.zip` exportado de AA360).

**Response `200`:**

```json
{
  "status": "success",
  "session_id": "20260416_102233_123456",
  "proyecto": "MiBot",
  "archivos_salida": {
    "calidad_path": "output/20260416_102233_123456/Calidad_MiBot.md",
    "calidad_word_path": "output/20260416_102233_123456/Calidad_MiBot.docx",
    "calidad_pdf_path": "output/20260416_102233_123456/Calidad_MiBot.pdf"
  },
  "output_directory": "output/20260416_102233_123456"
}
```

**Errores:** `400` validacion | `404` recurso no encontrado | `500` error interno

**Ejemplo:**

```bash
curl -X POST "http://localhost:8000/quality/" -F "file=@mi_bot.zip"
```

---

### `GET /download/{session_id}/{file_type}`

Descarga un artefacto generado. Responde con `application/octet-stream`.

**Path params:**
- `session_id`: valor devuelto por `/generate/` o `/quality/`
- `file_type`: uno de los tipos listados abajo

| `file_type` | Archivo descargado |
|-------------|-------------------|
| `sdd` | `SDD_<Proyecto>.md` |
| `sdd_word` | `SDD_<Proyecto>.docx` |
| `sdd_pdf` | `SDD_<Proyecto>.pdf` |
| `calidad` | `Calidad_<Proyecto>.md` |
| `calidad_word` | `Calidad_<Proyecto>.docx` |
| `calidad_pdf` | `Calidad_<Proyecto>.pdf` |
| `flujo_svg` | `flujo_taskbots.svg` |

**Errores:** `400` tipo invalido | `404` sesion/archivo no encontrado | `500` error interno

**Ejemplos:**

```bash
SESSION="20260416_102233_123456"
curl -O "http://localhost:8000/download/$SESSION/sdd"
curl -O "http://localhost:8000/download/$SESSION/sdd_pdf"
curl -O "http://localhost:8000/download/$SESSION/calidad_word"
curl -O "http://localhost:8000/download/$SESSION/flujo_svg"
```

---

## CORS

Origenes permitidos por defecto:

- `http://localhost`
- `http://localhost:3000`
- `http://localhost:8000`
- `http://127.0.0.1`
- `http://127.0.0.1:3000`

---

## Limites

| Parametro | Valor |
|-----------|-------|
| Tamano maximo ZIP | 500 MB |
| Tamano maximo extraccion | 1 GB |

> Estos limites son configurables via variables de entorno (`MAX_FILE_SIZE`, `MAX_EXTRACTION_SIZE`).

---

## Estructura del proyecto

```text
rpa-doc-generator/
├── app/
│   ├── main.py            # Bootstrap FastAPI (config, middleware, routers, docs)
│   ├── api/
│   │   ├── deps.py        # Dependencias compartidas (settings/logger)
│   │   └── routes/
│   │       ├── generate.py
│   │       ├── quality.py
│   │       ├── download.py
│   │       └── system.py
│   ├── application/
│   │   ├── settings.py    # Carga tipada de variables de entorno
│   │   └── use_cases/
│   │       ├── generate_sdd.py
│   │       ├── generate_quality.py
│   │       └── download_artifact.py
│   ├── ingestion/
│   │   ├── uploader.py    # Validacion y guardado del ZIP
│   │   └── extractor.py   # Extraccion segura del ZIP
│   ├── parser/
│   │   └── project_parser.py  # Parseo taskbots, variables, credenciales, sistemas
│   ├── analysis/
│   │   ├── flow_builder.py    # Grafo de dependencias entre taskbots
│   │   ├── tree_builder.py    # Arbol de directorios filtrado
│   │   └── task_ai_describer.py # Analisis IA (calidad + SDD)
│   ├── generator/
│   │   ├── sdd_generator.py   # Compilacion SDD y reporte de calidad (Markdown)
│   │   ├── diagram_generator.py  # SVG del flujo entre taskbots
│   │   ├── word_generator.py  # Exportacion DOCX
│   │   └── pdf_generator.py   # Exportacion PDF
│   ├── templates/
│   │   ├── sdd_template.md    # Plantilla Markdown del SDD
│   │   └── quality_template.md # Plantilla Markdown del reporte de calidad
│   └── static/
├── tests/
│   ├── test_api_structure.py
│   ├── test_routes_error_mapping.py
│   ├── test_use_cases_coverage.py
│   ├── test_uploader_tree_settings_coverage.py
│   ├── test_export_generators_coverage.py
│   ├── test_flow_ai_edge_coverage.py
│   ├── test_diagram_main_coverage.py
│   ├── test_parser_additional_coverage.py
│   ├── test_aa360_pipeline.py
│   ├── test_parser_quality_coverage.py
│   ├── test_extractor_coverage.py
│   ├── test_task_ai_describer.py
│   ├── test_template_loading.py
│   ├── test_quality_content_validation.py
│   └── test_sdd_content_validation.py
├── output/                # Artefactos generados por sesion
├── tmp/                   # ZIPs extraidos temporalmente
├── requirements.txt
├── .env.example
├── run.bat
├── run.sh
└── DEVELOPMENT.md
```

---

## Configuracion por entorno

- Runtime usa variables desde `.env`.
- `.env.example` es plantilla de referencia.
- Variables de IA, CORS, paths, host/puerto y limites de upload/extraccion se gestionan desde entorno.

---

## Flujo interno de procesamiento

```
1. Router HTTP recibe request (`app/api/routes/*`)
2. Caso de uso de aplicacion orquesta pipeline (`app/application/use_cases/*`)
3. Ingestion: validacion y guardado ZIP
4. Extraccion en tmp/
5. Parseo de manifest.json + deteccion de taskbots
6. Construccion de flujo/arbol
7. Compilacion de SDD o Calidad en Markdown
8. Exportacion a DOCX y PDF
9. Entrega de rutas en la respuesta JSON
```

---

## Troubleshooting

| Problema | Solucion |
|----------|----------|
| `400` al subir archivo | Verificar que sea un ZIP valido exportado de AA360 |
| `404` al descargar | Verificar `session_id` y que `file_type` sea valido |
| Puerto ocupado | Iniciar con `--port 8001` |
| Modulo no encontrado | `pip install -r requirements.txt` |
| Configuracion no aplicada | Verificar que el valor este en `.env` y reiniciar la API |

---

Para guia de desarrollo y arquitectura interna ver [DEVELOPMENT.md](DEVELOPMENT.md).
