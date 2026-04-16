@echo off
REM Script para ejecutar RPA Doc Generator en Windows

echo.
echo ========================================
echo RPA Doc Generator - Iniciando...
echo ========================================
echo.

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python no está instalado o no está en el PATH
    pause
    exit /b 1
)

REM Crear venv si no existe
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

REM Activar venv
echo Activando entorno virtual...
call venv\Scripts\activate.bat

REM Instalar dependencias si no existen
echo Verificando dependencias...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r requirements.txt
)

REM Crear directorios necesarios
if not exist "tmp" mkdir tmp
if not exist "output" mkdir output

echo.
echo Iniciando servidor FastAPI en http://localhost:8000
echo Presiona Ctrl+C para detener
echo.

REM Ejecutar la aplicación
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
