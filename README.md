# RPA Doc Generator

Generador automatico de documentacion SDD para bots de Automation Anywhere 360.

## Descripcion

**RPA Doc Generator** recibe un archivo ZIP exportado desde Automation Anywhere 360, analiza su contenido (manifest, taskbots, variables, dependencias) y genera un documento SDD (Software Design Document) en Markdown junto con un diagrama SVG del flujo entre taskbots.

### Caracteristicas

- Parseo del `manifest.json` para descubrir taskbots y dependencias reales.
- Deteccion automatica de taskbots por estructura JSON cuando no hay manifest.
- Extraccion de metadatos de cabecera (developer, fecha, descripcion) desde comentarios.
- Analisis de nodos AA360: condiciones, bucles, manejo de errores, invocaciones `runTask`.
- Inventario de variables de entrada, salida e internas con tipo, default y descripcion.
- Deteccion de sistemas externos (URLs, bases de datos, rutas de archivo).
- Inventario de paquetes AA360 con version.
- Diagrama SVG del flujo entre taskbots con layout automatico.
- Arbol de directorios filtrado (excluye metadata, .jar, imagenes).
- Sanitizacion de datos sensibles (credenciales, rutas de usuario).
- API REST con FastAPI y descarga de archivos generados.

---

## Inicio Rapido

### Requisitos

- Python 3.8+
- pip

### Instalacion

```bash
# Crear ambiente virtual
python -m venv venv

# Activar ambiente virtual
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API queda disponible en `http://localhost:8000`. Documentacion interactiva en `/docs`.

---

## API

### POST /generate/

Sube un ZIP exportado de AA360 y genera toda la documentacion.

```bash
curl -X POST "http://localhost:8000/generate/" -F "file=@bot.zip"
```

Respuesta:

```json
{
  "status": "success",
  "session_id": "20260415_143022_123456",
  "proyecto": "MiBot",
  "archivos_salida": {
    "sdd_path": "./output/.../SDD_MiBot.md",
    "flujo_svg_path": "./output/.../flujo_taskbots.svg",
    "estructura_path": "./output/.../estructura.txt",
    "resumen_path": "./output/.../resumen.json"
  },
  "output_directory": "./output/20260415_143022_123456"
}
```

### GET /download/{session_id}/{file_type}

Descarga un archivo generado. Tipos disponibles: `sdd`, `flujo_svg`, `estructura`, `resumen`.

```bash
curl -O "http://localhost:8000/download/20260415_143022_123456/sdd"
```

### GET /health

```bash
curl "http://localhost:8000/health"
```

---

## Estructura del Proyecto

```
rpa-doc-generator/
├── app/
│   ├── main.py                      # API FastAPI
│   ├── ingestion/
│   │   ├── uploader.py              # Validacion y guardado del ZIP
│   │   └── extractor.py             # Extraccion del contenido
│   ├── parser/
│   │   └── project_parser.py        # Parseo de manifest, taskbots, variables, nodos
│   ├── analysis/
│   │   ├── flow_builder.py          # Grafo de dependencias entre taskbots
│   │   └── tree_builder.py          # Arbol de directorios filtrado
│   ├── generator/
│   │   ├── diagram_generator.py     # SVG del flujo entre taskbots
│   │   └── sdd_generator.py         # Compilacion del documento SDD
│   └── templates/
│       └── sdd_template.md          # Plantilla Markdown del SDD
├── output/                           # Archivos generados por sesion
├── tmp/                              # Archivos temporales (ZIP extraidos)
└── requirements.txt
```

---

## Pipeline de Procesamiento

```
1. UPLOAD      Validacion del ZIP recibido
2. EXTRACT     Descompresion en carpeta temporal
3. PARSE       Lectura de manifest.json y deteccion de taskbots
4. ANALYZE     Construccion del flujo (nodos, aristas, dependencias)
5. TREE        Generacion del arbol de directorios filtrado
6. SVG         Creacion del diagrama de flujo entre taskbots
7. SDD         Compilacion del documento Markdown
```

---

## Contenido del SDD Generado

| Seccion | Contenido |
|---------|-----------|
| Informacion General | Nombre, descripcion, taskbots, entrypoints, paquetes usados |
| Estadisticas | Nodos AA360, condiciones, bucles, invocaciones runTask, manejo de errores |
| Flujo Principal | Imagen SVG con layout automatico de taskbots y sus dependencias |
| Inventario de Taskbots | Rol, ruta, developer, descripcion, pasos principales, subtasks invocadas |
| Contrato de Variables | Tablas de entrada/salida/internas por taskbot con tipo, default, descripcion |
| Credenciales y Vaults | Credenciales y credential vaults detectados en los taskbots |
| Paquetes AA360 | Tabla de paquetes con version |
| Estructura del Proyecto | Arbol visual de directorios y archivos con tamanos |

---

## Ejemplo con Python

```python
import requests

with open("bot.zip", "rb") as f:
    response = requests.post("http://localhost:8000/generate/", files={"file": f})

result = response.json()
print(f"Sesion: {result['session_id']}")
print(f"SDD:    {result['archivos_salida']['sdd_path']}")
```

---

## Dependencias

| Paquete | Uso |
|---------|-----|
| fastapi | Framework web |
| uvicorn | Servidor ASGI |
| python-multipart | Soporte multipart/form-data |
| pydantic | Validacion de datos |
| lxml | Procesamiento XML |
| pyyaml | Procesamiento YAML |
| python-dateutil | Utilidades de fecha |

---

## Troubleshooting

| Error | Solucion |
|-------|----------|
| "El archivo debe ser .zip" | Verifica que sea un ZIP valido de AA360 |
| "La ruta no existe" | Revisa los logs del servidor |
| Puerto en uso | Cambia el puerto: `--port 8001` |

