<!-- INSTRUCCIONES RÁPIDAS PARA GENERAR DOCUMENTACIÓN -->

# 🚀 Guía Rápida - RPA Doc Generator

## 1. Iniciar el Servidor

### Windows
```bash
run.bat
```

### Linux/Mac
```bash
chmod +x run.sh
./run.sh
```

### Manual
```bash
python -m venv venv
venv\Scripts\activate  # Windows o source venv/bin/activate en Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Resultado:** Servidor disponible en `http://localhost:8000`

---

## 2. Generar Documentación

### Opción A: Con cURL

```bash
# Generar
curl -X POST "http://localhost:8000/generate/" \
  -F "file=@tu_bot.zip" \
  > response.json

# Ver respuesta
cat response.json

# Extraer session_id
SESSION_ID=$(jq -r '.session_id' response.json)
echo "Session: $SESSION_ID"
```

### Opción B: Con Python

```python
import requests
import json

# Generar
with open('tu_bot.zip', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/generate/',
        files={'file': f}
    )

result = response.json()

# Guardar respuesta
with open('respuesta.json', 'w') as f:
    json.dump(result, f, indent=2)

print(f"✓ Generado en: {result['output_directory']}")
print(f"✓ Tareas: {result['tareas']}")
print(f"✓ Session ID: {result['session_id']}")
```

### Opción C: Interface Web (Próximo)

Acceder a: `http://localhost:8000/docs` (Swagger UI)

---

## 3. Descargar Archivos Generados

```bash
# Reemplazar SESSION_ID con el ID de tu sesión
SESSION_ID="20260415_143022_123456"

# Descargar SDD (Markdown)
curl -O "http://localhost:8000/download/$SESSION_ID/sdd"

# Descargar Diagrama (Mermaid)
curl -O "http://localhost:8000/download/$SESSION_ID/diagrama"

# Descargar Estructura (Texto)
curl -O "http://localhost:8000/download/$SESSION_ID/estructura"

# Descargar Resumen (JSON)
curl -O "http://localhost:8000/download/$SESSION_ID/resumen"
```

---

## 4. Archivos Generados por Sesión

### Directorio: `./output/{SESSION_ID}/`

```
output/20260415_143022_123456/
├── SDD_NombreBot.md      # 📄 Documento completo (principal)
├── diagrama.mmd          # 📊 Diagrama del flujo
├── estructura.txt        # 📁 Árbol de directorios
└── resumen.json          # 📋 Resumen en JSON
```

### Contenido del SDD_NombreBot.md

```markdown
# SDD - NombreBot

## 1. Información General
(Detalles generales del bot)

## 2. Estadísticas
- Total de tareas: X
- Archivos XML: Y
- Archivos JSON: Z
...

## 3. Estructura del Proyecto
(Árbol de directorios - SIN metadata, SIN .jar)

## 4. Flujo de Procesos
(Diagrama Mermaid para visualizar visualmente)

## 5. Detalle de Tareas
### 1. NombreTarea.xml
**Tipo:** xml | **Tamaño:** 2.5 KB
**Descripción:** Qué hace esta tarea
**Pasos/Acciones:**
- ...

### 2. OtraTarea.xml
...

## 6. Variables de Entrada y Salida
### NombreTarea
**Variables de Entrada:**
| Nombre | Tipo | Valor |
| --- | --- | --- |
| usuario | String | |
| password | String | |

**Variables de Salida:**
| Nombre | Tipo | Valor |
| --- | --- | --- |
| resultado | Boolean | |

## 7. Metadatos
(Información del proyecto)
```

---

## 5. Qué es Nuevo en v1.1.0 🎉

✅ **Metadata excluida** - No incluye carpetas `metadata/`  
✅ **Sin archivos .jar** - Más limpio y relevante  
✅ **Diagrama visible** - Bloques mermaid correctamente formateados  
✅ **Descripción de tareas** - Qué hace cada tarea  
✅ **Tabla de variables** - Variables de entrada/salida con tipos  

---

## 6. Verificar que Todo Funciona

```bash
# Verificar salud del servicio
curl http://localhost:8000/health

# Respuesta esperada:
# {
#   "status": "healthy",
#   "app": "RPA Doc Generator",
#   "version": "1.0.0",
#   "timestamp": "2026-04-15T14:30:22.123456"
# }
```

---

## 7. Solución de Problemas

### "Puerto en uso"
```bash
# Cambiar puerto
uvicorn app.main:app --port 8001
```

### "Módulo no encontrado"
```bash
# Reinstalar dependencias
pip install -r requirements.txt
```

### "Archivo ZIP corrupto"
```bash
# Verificar que sea un ZIP válido
# Usar: 7z a bot.zip carpeta_bot/
```

### "No se ve el diagrama"
- ✅ Verificar que sea formato mermaid (bloques ``` ``` ` )
- ✅ Mostrar en editor que soporte mermaid (VS Code + extensión)
- ✅ O copiar a: https://mermaid.live/

---

## 8. Próximos Pasos

1. ✅ Generar SDD
2. 📥 Descargar archivos
3. 📝 Revisar documentación
4. 🔄 Iterar y mejorar
5. 📊 Compartir con equipo

---

## 📞 Ayuda Rápida

| Problema | Solución |
|----------|----------|
| Servidor no inicia | Verifica Python 3.8+, pip install -r requirements.txt |
| Error al subir ZIP | Confirma que sea archivo .zip válido |
| No hay variables en tabla | El archivo XML/JSON no incluye variables (optional) |
| Diagrama no se muestra | Ver en: https://mermaid.live/ |

---

**¡Listo para documentar bots!** 🤖📚
