# Development Guide

Guia tecnica interna de RPA Doc Generator.
Para instalacion, ejecucion y uso de la API ver [README.md](README.md).

---

## Arquitectura de modulos

### `app/ingestion/`

- `uploader.py` — Recibe el `UploadFile` de FastAPI, valida extension y lo guarda en `tmp/`.
- `extractor.py` — Descomprime el ZIP de forma segura (previene path traversal). Retorna la ruta de la carpeta extraida.

### `app/parser/`

- `project_parser.py` — Punto de entrada: `parse_project(path)`.
  - Carga `manifest.json` para descubrir taskbots por `contentType`.
  - Fallback: escanea el directorio buscando JSONs con las claves `nodes`, `variables`, `packages`, `properties`.
  - Extrae por taskbot: variables input/output/internas, nodos AA360, llamadas `runTask`, credenciales, sistemas externos, comentarios de cabecera (developer, fecha, descripcion).
  - Retorna un dict estructurado con `tasks`, `packages`, `systems`, `credentials`, `metadata`, `files`.

### `app/analysis/`

- `flow_builder.py` — Construye nodos y aristas a partir de las dependencias `scannedDependencies` del manifest y de las llamadas `runTask` detectadas. Retorna `{nodes, edges, summary}`.
- `tree_builder.py` — Genera un arbol de directorios como texto, filtrando carpetas `metadata`, archivos `.jar`, imagenes, cache y archivos ocultos.

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

Archivo: `tests/test_aa360_pipeline.py`

Cubre:
- Pipeline completo con proyecto AA360 sintetico (Main → Lookup con contrato de variables).
- Validacion de path traversal al extraer ZIPs maliciosos.

Ejecutar:

```bash
python -m pytest -q
```

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
