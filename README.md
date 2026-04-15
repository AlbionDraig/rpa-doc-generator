# RPA Doc Generator 🤖📚

*Generador automático de documentación SDD para bots de Automation Anywhere*

## 📋 Descripción

**RPA Doc Generator** es una herramienta que automatiza la creación de documentación de diseño (SDD - Software Design Document) a partir de archivos ZIP de bots desarrollados en Automation Anywhere.

### Características

✅ **Extracción automática** de archivos ZIP  
✅ **Análisis inteligente** de estructura y tareas  
✅ **Generación de diagramas** con Mermaid  
✅ **Documentación completa** en formato Markdown  
✅ **Estadísticas detalladas** del proyecto  
✅ **API REST** con FastAPI  
✅ **Manejo robusto de errores** y logging  
✅ **Descarga de archivos generados**  

---

## 🚀 Inicio Rápido

### 1. Requisitos Previos

- Python 3.8+
- pip
- Un archivo ZIP de un bot de Automation Anywhere

### 2. Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt
```

### 3. Ejecutar la Aplicación

```bash
# Opción 1: Con Python directamente
python app/main.py

# Opción 2: Con uvicorn (recomendado)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La aplicación estará disponible en: `http://localhost:8000`

---

## 📖 Documentación de la API

### Endpoints Principales

#### 1. **POST /generate/** - Generar Documentación
Genera la documentación SDD completa para un bot.

**Request:**
```bash
curl -X POST "http://localhost:8000/generate/" \
  -F "file=@tu_bot.zip"
```

**Response:**
```json
{
  "status": "success",
  "session_id": "20240415_143022_123456",
  "proyecto": "Mi Bot RPA",
  "tareas": 15,
  "archivos_salida": {
    "sdd_path": "./output/.../SDD_Mi_Bot_RPA.md",
    "diagrama_path": "./output/.../diagrama.mmp",
    "estructura_path": "./output/.../estructura.txt",
    "resumen_path": "./output/.../resumen.json"
  },
  "output_directory": "./output/20240415_143022_123456"
}
```

#### 2. **GET /download/{session_id}/{file_type}** - Descargar Archivos
Descarga los archivos generados.

**Tipos de archivo disponibles:**
- `sdd`: Documento SDD completo en Markdown
- `diagrama`: Diagrama Mermaid del flujo
- `estructura`: Árbol de directorios en texto
- `resumen`: Resumen en formato JSON

**Ejemplo:**
```bash
curl -O "http://localhost:8000/download/20240415_143022_123456/sdd"
```

#### 3. **GET /health** - Verificar Estado
```bash
curl "http://localhost:8000/health"
```

---

## 📁 Estructura del Proyecto

```
rpa-doc-generator/
├── app/
│   ├── main.py                      # API FastAPI principal
│   ├── config.py                    # Configuración
│   ├── utils.py                     # Utilidades comunes
│   ├── ingestion/
│   │   ├── uploader.py              # Carga de archivos ZIP
│   │   └── extractor.py             # Extracción de contenido
│   ├── parser/
│   │   └── project_parser.py        # Análisis de estructura
│   ├── analysis/
│   │   ├── flow_builder.py          # Construcción de flujos
│   │   └── tree_builder.py          # Árbol de directorios
│   ├── generator/
│   │   ├── diagram_generator.py     # Generador de diagramas Mermaid
│   │   └── sdd_generator.py         # Generador de SDD
│   └── templates/
│       └── sdd_template.md          # Plantilla SDD
├── output/                           # Archivos generados
├── tmp/                              # Archivos temporales
└── requirements.txt                 # Dependencias
```

---

## 🔄 Flujo de Procesamiento

```
1. CARGA     → Validación del ZIP
2. EXTRACCIÓN → Descompresión en carpeta temporal
3. ANÁLISIS  → Parseo de estructura y tareas
4. GENERACIÓN → Creación de diagramas y documentación
5. SALIDA    → Guardado de archivos generados
```

---

## 📊 Contenido del SDD Generado

El documento SDD incluye:

1. **Información General**
   - Nombre del bot
   - Descripción
   - Fecha de generación

2. **Estadísticas**
   - Total de tareas
   - Cantidad de archivos XML/JSON
   - Estadísticas de flujo

3. **Estructura**
   - Árbol de directorios visual
   - Tamaños de archivo

4. **Flujo de Procesos**
   - Diagrama Mermaid interactivo
   - Visualización del flujo de ejecución

5. **Detalles de Tareas**
   - Información de cada tarea
   - Tipos y tamaños de archivo

---

## 💻 Ejemplos de Uso

### Con FastAPI/Python

```python
# La API automáticamente procesará el archivo POST
# Ver ejemplos de cURL abajo
```

### Con cURL

```bash
# 1. Generar documentación
curl -X POST "http://localhost:8000/generate/" \
  -F "file=@mi_bot.zip" \
  -o response.json | jq

# 2. Extraer session_id
SESSION_ID=$(jq -r '.session_id' response.json)

# 3. Descargar archivos
curl -O "http://localhost:8000/download/$SESSION_ID/sdd"
curl -O "http://localhost:8000/download/$SESSION_ID/diagrama"
curl -O "http://localhost:8000/download/$SESSION_ID/resumen"
```

### Con Python requests

```python
import requests
import json

# Generar documentación
with open('bot.zip', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/generate/', files=files)

result = response.json()
session_id = result['session_id']

print(f"✓ Documentación generada: {session_id}")
print(f"  Tareas encontradas: {result['tareas']}")
print(f"  Salida en: {result['output_directory']}")
```

---

## 🛠️ Mejoras Implementadas

✨ **Nuevas Características:**
- ✅ Manejo robusto de errores con try-catch
- ✅ Logging comprehensive de todas las operaciones
- ✅ Validación de archivos ZIP
- ✅ Parseo mejorado de XML/JSON
- ✅ Estadísticas detalladas del proyecto
- ✅ Generación de múltiples formatos de salida
- ✅ API con docstring y ejemplos
- ✅ Organización en sesiones con timestamp unique
- ✅ Descarga de archivos generados
- ✅ Configuración centralizada
- ✅ Utilidades comunes reutilizables
- ✅ Documentación completa

---

## 📦 Dependencias

```
fastapi          # Framework web moderno
uvicorn          # Servidor ASGI
python-multipart # Multipart/form-data
pydantic         # Validación de datos
lxml             # Procesamiento de XML
pyyaml           # Procesamiento de YAML
python-dateutil  # Utilidades de fecha
```

---

## 🐛 Troubleshooting

| Error | Solución |
|-------|----------|
| "El archivo debe ser .zip" | Verifica que sea un ZIP válido |
| "La ruta no existe" | Revisa los logs para detalles |
| "Plantilla no encontrada" | Asegúrate que `sdd_template.md` existe |
| Puerto en uso | Cambia el puerto: `--port 8001` |

---

## 📝 Próximas Mejoras

- [ ] Generación de PDF desde Markdown
- [ ] Autenticación y autorización
- [ ] Interfaz web de usuario
- [ ] Historial de generaciones
- [ ] Búsqueda en documentos generados
- [ ] Exportación a múltiples formatos

---

## 📧 Soporte

Para reportar bugs o pedir features, abre un issue en el repositorio.

---

**Desarrollado con ❤️ para la automatización empresarial**

