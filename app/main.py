import logging
import os
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.ingestion.uploader import save_file
from app.ingestion.extractor import extract_project
from app.parser.project_parser import parse_project
from app.analysis.flow_builder import build_flow
from app.analysis.tree_builder import build_tree
from app.generator.diagram_generator import generate_mermaid
from app.generator.sdd_generator import generate_sdd, generate_sdd_file

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="RPA Doc Generator",
    description="Generador automático de documentación SDD para bots de Automation Anywhere",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear directorios necesarios
Path("./output").mkdir(exist_ok=True)
Path("./tmp").mkdir(exist_ok=True)

logger.info("=" * 60)
logger.info("RPA Doc Generator - API iniciada")
logger.info("=" * 60)


@app.post("/generate/")
async def generate(file: UploadFile):
    """
    Genera documentación SDD para un bot de Automation Anywhere.
    
    **Parámetros:**
    - file: Archivo ZIP del bot (requerido)
    
    **Response:**
    - status: Estado de la operación
    - session_id: ID único de la sesión
    - proyecto: Nombre del proyecto
    - tareas: Total de tareas encontradas
    - archivos_salida: Rutas de los archivos generados
    
    **Errores:**
    - 400: Archivo inválido o vacío
    - 413: Archivo demasiado grande
    - 500: Error interno del servidor
    
    **Ejemplo cURL:**
    ```
    curl -X POST "http://localhost:8000/generate/" \\
      -F "file=@bot.zip"
    ```
    """
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = Path("./output") / session_id
    
    try:
        logger.info(f"[START] Procesando archivo: {file.filename} - Sesión: {session_id}")
        
        # Paso 1: Guardar archivo
        logger.info(f"[1/8] Guardando archivo...")
        zip_path = save_file(file)
        
        # Paso 2: Extraer proyecto
        logger.info(f"[2/8] Extrayendo contenido...")
        project_path = extract_project(zip_path)
        
        # Paso 3: Parsear proyecto
        logger.info(f"[3/8] Analizando estructura...")
        project_data = parse_project(project_path)
        logger.info(f"     Tareas encontradas: {project_data['task_count']}")
        
        # Paso 4: Construir flujo
        logger.info(f"[4/8] Construyendo flujo...")
        flow = build_flow(project_data["tasks"])
        
        # Paso 5: Construir árbol
        logger.info(f"[5/8] Generando estructura...")
        tree = build_tree(project_path)
        
        # Paso 6: Generar diagrama
        logger.info(f"[6/8] Creando diagrama...")
        diagram = generate_mermaid(flow)
        
        # Paso 7: Generar SDD
        logger.info(f"[7/8] Generando documentación...")
        sdd = generate_sdd(project_data, tree, diagram, flow)
        
        # Paso 8: Guardar archivos de salida
        logger.info(f"[8/8] Guardando archivos...")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar SDD en archivo
        sdd_file = output_dir / f"SDD_{project_data['name']}.md"
        generate_sdd_file(project_data, tree, diagram, str(sdd_file), flow)
        
        # Guardar diagrama en archivo
        diagram_file = output_dir / "diagrama.mmd"
        with open(diagram_file, 'w', encoding='utf-8') as f:
            f.write(diagram)
        
        # Guardar árbol en archivo
        tree_file = output_dir / "estructura.txt"
        with open(tree_file, 'w', encoding='utf-8') as f:
            f.write(tree)
        
        # Guardar resumen JSON
        import json
        summary_file = output_dir / "resumen.json"
        summary = {
            "nombre_proyecto": project_data["name"],
            "total_tareas": project_data["task_count"],
            "archivos_xml": project_data["files"]["xml_count"],
            "archivos_json": project_data["files"]["json_count"],
            "nodos_flujo": flow["summary"]["total_nodes"],
            "conexiones": flow["summary"]["total_edges"],
            "fecha_generacion": datetime.now().isoformat(),
            "archivos_salida": {
                "sdd": str(sdd_file),
                "diagrama": str(diagram_file),
                "estructura": str(tree_file),
                "resumen": str(summary_file)
            }
        }
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[COMPLETE] Procesamiento finalizado - Sesión: {session_id}")
        
        return {
            "status": "success",
            "session_id": session_id,
            "proyecto": project_data["name"],
            "tareas": project_data["task_count"],
            "archivos_xml": project_data["files"]["xml_count"],
            "archivos_json": project_data["files"]["json_count"],
            "arbol": tree,
            "diagrama": diagram,
            "sdd": sdd,
            "archivos_salida": {
                "sdd_path": str(sdd_file),
                "diagrama_path": str(diagram_file),
                "estructura_path": str(tree_file),
                "resumen_path": str(summary_file)
            },
            "output_directory": str(output_dir)
        }
    
    except ValueError as e:
        logger.error(f"[ERROR] Validación: {str(e)} - Sesión: {session_id}")
        raise HTTPException(status_code=400, detail=f"Error de validación: {str(e)}")
    except FileNotFoundError as e:
        logger.error(f"[ERROR] Archivo no encontrado: {str(e)} - Sesión: {session_id}")
        raise HTTPException(status_code=404, detail=f"No encontrado: {str(e)}")
    except Exception as e:
        logger.error(f"[ERROR] Inesperado: {str(e)} - Sesión: {session_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.get("/download/{session_id}/{file_type}")
async def download_file(session_id: str, file_type: str):
    """
    Descarga un archivo generado de una sesión.
    
    **Parámetros:**
    - session_id: ID de la sesión (desde /generate/)
    - file_type: Tipo de archivo (sdd, diagrama, estructura, resumen)
    
    **Archivos disponibles:**
    - sdd: Documento SDD completo en Markdown
    - diagrama: Diagrama del flujo en Mermaid
    - estructura: Árbol de directorios en texto
    - resumen: Información en JSON
    
    **Errores:**
    - 400: Tipo de archivo inválido
    - 404: Archivo no encontrado
    
    **Ejemplo cURL:**
    ```
    curl -O "http://localhost:8000/download/20240415_143022_123456/sdd"
    ```
    """
    output_dir = Path("./output") / session_id
    
    file_map = {
        "sdd": lambda: list(output_dir.glob("SDD_*.md"))[0] if list(output_dir.glob("SDD_*.md")) else None,
        "diagrama": lambda: output_dir / "diagrama.mmp",
        "estructura": lambda: output_dir / "estructura.txt",
        "resumen": lambda: output_dir / "resumen.json"
    }
    
    if file_type not in file_map:
        logger.warning(f"[WARNING] Tipo de archivo inválido: {file_type}")
        raise HTTPException(status_code=400, detail="Tipo de archivo inválido")
    
    try:
        file_path = file_map[file_type]()
        
        if file_path is None or not file_path.exists():
            logger.warning(f"[WARNING] Archivo no encontrado: {file_type} - Sesión: {session_id}")
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        logger.info(f"[DOWNLOAD] {file_type} - Sesión: {session_id}")
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/octet-stream"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Descargando archivo: {str(e)} - Sesión: {session_id}")
        raise HTTPException(status_code=500, detail="Error al descargar archivo")


@app.get("/health")
async def health():
    """
    Verifica que la aplicación esté en funcionamiento.
    
    **Response:**
    - status: Estado de la aplicación
    - app: Nombre de la aplicación
    - version: Versión
    - timestamp: Fecha y hora del servidor
    
    **Ejemplo cURL:**
    ```
    curl "http://localhost:8000/health"
    ```
    """
    return {
        "status": "healthy",
        "app": "RPA Doc Generator",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """
    Página raíz de la API.
    Redirige a la documentación.
    """
    return {
        "message": "RPA Doc Generator API",
        "version": "1.0.0",
        "docs": "http://localhost:8000/docs",
        "redoc": "http://localhost:8000/redoc",
        "health": "http://localhost:8000/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )

