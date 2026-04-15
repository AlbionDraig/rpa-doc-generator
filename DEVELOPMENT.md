# RPA Doc Generator - Guía de Desarrollo

## 🔧 Configuración del Entorno de Desarrollo

### Requisitos
- Python 3.8+
- pip
- Git
- Editor de código (VS Code recomendado)

### Setup Inicial

```bash
# 1. Clonar repositorio
git clone <url>
cd rpa-doc-generator

# 2. Crear virtual environment
python -m venv venv

# 3. Activar virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Instalar dependencias de desarrollo (opcional)
pip install pytest pytest-cov black flake8 mypy
```

---

## 📝 Estructura de Módulos

### `app/ingestion/`
**Responsabilidad:** Carga y validación de archivos

- `uploader.py` - Guardar archivos ZIP subidos
- `extractor.py` - Descompresión y validación de ZIP

**Agregar nueva funcionalidad:**
```python
# Ejemplo: validar tamaño de archivo
def validate_file_size(file, max_size):
    content = file.file.read()
    if len(content) > max_size:
        raise ValueError("Archivo demasiado grande")
    return len(content)
```

### `app/parser/`
**Responsabilidad:** Análisis de estructura del proyecto

- `project_parser.py` - Parseo de XML/JSON y extracción de metadatos

**Agregar nueva funcionalidad:**
```python
# Ejemplo: extraer variables del proyecto
def extract_variables(project_path):
    variables = []
    for xml_file in find_xml_files(project_path):
        # Procesar y extraer variables
        pass
    return variables
```

### `app/analysis/`
**Responsabilidad:** Análisis de flujos y estructura

- `flow_builder.py` - Construcción del flujo de procesos
- `tree_builder.py` - Generación del árbol visual

**Agregar nueva funcionalidad:**
```python
# Ejemplo: detectar bucles en el flujo
def detect_loops(flow):
    loops = []
    # Análisis de ciclos
    return loops
```

### `app/generator/`
**Responsabilidad:** Generación de documentos y diagramas

- `diagram_generator.py` - Crear diagramas Mermaid
- `sdd_generator.py` - Compilar documento SDD

**Agregar nueva funcionalidad:**
```python
# Ejemplo: generar PDF desde MD
def generate_pdf(markdown_content, output_path):
    # Usar pandoc o similar
    pass
```

---

## 🧪 Testing

### Estructura de Tests

```
tests/
├── test_ingestion.py
├── test_parser.py
├── test_analysis.py
├── test_generator.py
└── test_api.py
```

### Ejemplo de Test

```python
import pytest
from app.ingestion.extractor import extract_project

def test_extract_valid_zip():
    # Arrange
    test_zip = "tests/fixtures/test_bot.zip"
    
    # Act
    result = extract_project(test_zip)
    
    # Assert
    assert result is not None
    assert os.path.isdir(result)
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=app

# Tests específicos
pytest tests/test_parser.py -v
```

---

## 📚 Mejoras Sugeridas

### Corto Plazo (Sprint 1)
- [ ] Agregar tests unitarios
- [ ] Validación de esquema XML
- [ ] Caché de proyectos procesados
- [ ] Límite de tasa (rate limiting)

### Mediano Plazo (Sprint 2-3)
- [ ] Generación de PDF desde SDD
- [ ] Interfaz web (frontend)
- [ ] Autenticación y autorización
- [ ] Base de datos para historial
- [ ] Búsqueda en documentos

### Largo Plazo (Sprint 4+)
- [ ] Exportación a Azure Devops
- [ ] Integración con Git
- [ ] Versionado de documentos
- [ ] Colaboración en tiempo real
- [ ] Webhooks para automatización

---

## 🔍 Debugging

### Ver Logs Detallados
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

### Print Statements
```python
# Útil para debugging rápido
print(f"DEBUG: variable = {variable}")
```

### Usar el Debugger de Python
```python
import pdb; pdb.set_trace()  # Se pausará aquí

# O con VS Code:
# Agregar breakpoint en el código y F5
```

---

## 📋 Convenciones de Código

### Nombrado
```python
# ✓ Bueno
def generate_sdd_document(project_data):
    pass

# ✗ Evitar
def gen_sdd(d):
    pass
```

### Docstrings
```python
def extract_project(zip_path):
    """
    Extrae el contenido del ZIP del bot.
    
    Args:
        zip_path (str): Ruta del archivo ZIP
        
    Returns:
        str: Ruta de la carpeta extraída
        
    Raises:
        FileNotFoundError: Si el ZIP no existe
        zipfile.BadZipFile: Si el ZIP está corrompido
    """
    pass
```

### Type Hints (Python 3.8+)
```python
from typing import Dict, List, Optional

def parse_project(path: str) -> Dict[str, any]:
    """Parse project information."""
    pass
```

---

## 🚀 Deployment

### Producción con Docker

```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Deployment en Heroku

```bash
# 1. Crear Procfile
echo "web: uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-8000}" > Procfile

# 2. Deploy
heroku create rpa-doc-generator
git push heroku main
```

---

## 📧 Preguntas Frecuentes

**P: ¿Cómo agregar soporte para nuevos formatos?**  
R: Extender `project_parser.py` con nuevas funciones de parseo.

**P: ¿Cómo mejorar la velocidad?**  
R: Implementar caché, procesamiento async, o paralelización.

**P: ¿Cómo manejar proyectos muy grandes?**  
R: Usar streaming, procesar en chunks, o dividir en subtareas.

---

## 💡 Tips

1. **Utiliza logging:** Mejor que print() para producción
2. **Valida entrada:** Siempre validar datos antes de procesarlos
3. **Documenta:** Docstrings y comentarios claros
4. **Testa:** Escribe tests para nuevas features
5. **Refactoriza:** Mejora continuamente el código

---

**¡Feliz desarrollo!** 🎉
