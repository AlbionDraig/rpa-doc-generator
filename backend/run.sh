#!/bin/bash
# Script para ejecutar RPA Doc Generator en Linux/Mac
# Ejecutar desde la raiz del repositorio: bash backend/run.sh

echo ""
echo "========================================"
echo "RPA Doc Generator - Iniciando..."
echo "========================================"
echo ""

# Cambiar al directorio del script (backend/)
cd "$(dirname "$0")"

# Verificar que Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no está instalado"
    exit 1
fi

# Crear venv en la raiz del repo (un nivel arriba)
if [ ! -d "../venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv ../venv
fi

# Activar venv
echo "Activando entorno virtual..."
source ../venv/bin/activate

# Instalar dependencias si no existen
echo "Verificando dependencias..."
pip show fastapi > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Instalando dependencias..."
    pip install -r requirements.txt
fi

# Crear directorios necesarios en la raiz del repo
mkdir -p ../tmp
mkdir -p ../output

echo ""
echo "Iniciando servidor FastAPI en http://localhost:8000"
echo "Presiona Ctrl+C para detener"
echo ""

# Ejecutar la aplicación desde backend/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
