# RPA Doc Generator

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
| `AI_QUALITY_ENABLED` | Habilita inferencia con IA (`true/false`) | `false` |
| `GROQ_API_KEY` | API key de Groq | - |
| `GROQ_MODEL` | Modelo Groq para la interpretacion | `llama-3.3-70b-versatile` |
| `GROQ_BASE_URL` | Base URL de Groq compatible con OpenAI | `https://api.groq.com/openai/v1` |
| `OPENAI_API_KEY` | API key para endpoint compatible con OpenAI | - |
| `OPENAI_MODEL` | Modelo de chat a utilizar | `gpt-4o-mini` |
| `OPENAI_BASE_URL` | Base URL del proveedor compatible (`.../v1`) | `https://api.openai.com/v1` |
| `AI_TIMEOUT_SECONDS` | Timeout por llamada de IA | `25` |

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
| Extensiones internas procesadas | `.xml`, `.json`, `.txt`, `.yml`, `.yaml`, `.csv` |

---

## Estructura del proyecto

```text
rpa-doc-generator/
├── app/
│   ├── main.py            # API FastAPI (endpoints)
│   ├── config.py          # Configuracion y limites
│   ├── ingestion/
│   │   ├── uploader.py    # Validacion y guardado del ZIP
│   │   └── extractor.py   # Extraccion segura del ZIP
│   ├── parser/
│   │   └── project_parser.py  # Parseo taskbots, variables, credenciales, sistemas
│   ├── analysis/
│   │   ├── flow_builder.py    # Grafo de dependencias entre taskbots
│   │   └── tree_builder.py    # Arbol de directorios filtrado
│   ├── generator/
│   │   ├── sdd_generator.py   # Compilacion SDD y reporte de calidad (Markdown)
│   │   ├── diagram_generator.py  # SVG del flujo entre taskbots
│   │   ├── word_generator.py  # Exportacion DOCX
│   │   └── pdf_generator.py   # Exportacion PDF
│   ├── templates/
│   │   └── sdd_template.md    # Plantilla Markdown del SDD
│   └── static/
├── tests/
│   └── test_aa360_pipeline.py
├── output/                # Artefactos generados por sesion
├── tmp/                   # ZIPs extraidos temporalmente
├── requirements.txt
├── run.bat
├── run.sh
└── DEVELOPMENT.md
```

---

## Flujo interno de procesamiento

```
1. Validacion y guardado del ZIP
2. Extraccion en tmp/
3. Parseo de manifest.json + deteccion de taskbots
4. Construccion del grafo de dependencias
5. Generacion del arbol de directorios filtrado
6. Render del flujo SVG (+ conversion PNG intermedia para DOCX/PDF)
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

---

Para guia de desarrollo y arquitectura interna ver [DEVELOPMENT.md](DEVELOPMENT.md).
