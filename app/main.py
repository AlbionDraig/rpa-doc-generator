import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.analysis.flow_builder import build_flow
from app.analysis.tree_builder import build_tree
from app.generator.diagram_generator import generate_flow_svg
from app.generator.sdd_generator import generate_sdd, generate_sdd_file
from app.ingestion.extractor import extract_project
from app.ingestion.uploader import save_file
from app.parser.project_parser import parse_project

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RPA Doc Generator",
    description="Generador automatico de documentacion SDD para bots de Automation Anywhere",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path("./output").mkdir(exist_ok=True)
Path("./tmp").mkdir(exist_ok=True)

logger.info("=" * 60)
logger.info("RPA Doc Generator - API iniciada")
logger.info("=" * 60)


@app.post("/generate/")
async def generate(file: UploadFile):
    """
    Genera documentacion SDD para un bot de Automation Anywhere.
    """
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = Path("./output") / session_id

    try:
        logger.info("[START] Procesando archivo: %s - Sesion: %s", file.filename, session_id)

        logger.info("[1/7] Guardando archivo...")
        zip_path = save_file(file)

        logger.info("[2/7] Extrayendo contenido...")
        project_path = extract_project(zip_path)

        logger.info("[3/7] Analizando estructura...")
        project_data = parse_project(project_path)
        logger.info("     Taskbots encontrados: %s", project_data["task_count"])

        logger.info("[4/7] Construyendo flujo...")
        flow = build_flow(project_data["tasks"])

        logger.info("[5/7] Generando estructura...")
        tree = build_tree(project_path)

        logger.info("[6/7] Generando recursos visuales...")
        output_dir.mkdir(parents=True, exist_ok=True)

        flow_svg = generate_flow_svg(flow)
        flow_svg_file = output_dir / "flujo_taskbots.svg"
        flow_svg_file.write_text(flow_svg, encoding="utf-8")

        flow_visual = "\n".join(
            [
                "![Flujo principal entre taskbots](flujo_taskbots.svg)",
                "",
                "_La imagen muestra entrypoints, direccion de invocacion y el contrato resumido por flecha cuando aplica._",
            ]
        )

        logger.info("[7/7] Generando documentacion...")
        sdd = generate_sdd(project_data, tree, flow, flow_visual)

        sdd_file = output_dir / f"SDD_{project_data['name']}.md"
        generate_sdd_file(project_data, tree, str(sdd_file), flow, flow_visual)

        tree_file = output_dir / "estructura.txt"
        tree_file.write_text(tree, encoding="utf-8")

        summary_file = output_dir / "resumen.json"
        summary = {
            "nombre_proyecto": project_data["name"],
            "total_taskbots": project_data["task_count"],
            "total_tareas": project_data["task_count"],
            "entrypoints": project_data.get("metadata", {}).get("entrypoints", []),
            "archivos_xml": project_data["files"]["xml_count"],
            "archivos_json": project_data["files"]["json_count"],
            "paquetes_detectados": len(project_data.get("packages", [])),
            "sistemas_detectados": len(project_data.get("systems", [])),
            "credenciales_detectadas": len(project_data.get("credentials", [])),
            "nodos_flujo": flow["summary"]["total_nodes"],
            "conexiones": flow["summary"]["total_edges"],
            "fecha_generacion": datetime.now().isoformat(),
            "archivos_salida": {
                "sdd": str(sdd_file),
                "flujo_svg": str(flow_svg_file),
                "estructura": str(tree_file),
                "resumen": str(summary_file),
            },
        }
        summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info("[COMPLETE] Procesamiento finalizado - Sesion: %s", session_id)

        return {
            "status": "success",
            "session_id": session_id,
            "proyecto": project_data["name"],
            "archivos_salida": {
                "sdd_path": str(sdd_file),
                "flujo_svg_path": str(flow_svg_file),
                "estructura_path": str(tree_file),
                "resumen_path": str(summary_file),
            },
            "output_directory": str(output_dir),
        }

    except ValueError as exc:
        logger.error("[ERROR] Validacion: %s - Sesion: %s", exc, session_id)
        raise HTTPException(status_code=400, detail=f"Error de validacion: {exc}") from exc
    except FileNotFoundError as exc:
        logger.error("[ERROR] Archivo no encontrado: %s - Sesion: %s", exc, session_id)
        raise HTTPException(status_code=404, detail=f"No encontrado: {exc}") from exc
    except Exception as exc:
        logger.error("[ERROR] Inesperado: %s - Sesion: %s", exc, session_id, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {exc}") from exc


@app.get("/download/{session_id}/{file_type}")
async def download_file(session_id: str, file_type: str):
    """
    Descarga un archivo generado de una sesion.
    """
    output_dir = Path("./output") / session_id

    file_map = {
        "sdd": lambda: list(output_dir.glob("SDD_*.md"))[0] if list(output_dir.glob("SDD_*.md")) else None,
        "flujo_svg": lambda: output_dir / "flujo_taskbots.svg",
        "estructura": lambda: output_dir / "estructura.txt",
        "resumen": lambda: output_dir / "resumen.json",
    }

    if file_type not in file_map:
        logger.warning("[WARNING] Tipo de archivo invalido: %s", file_type)
        raise HTTPException(status_code=400, detail="Tipo de archivo invalido")

    try:
        file_path = file_map[file_type]()
        if file_path is None or not file_path.exists():
            logger.warning("[WARNING] Archivo no encontrado: %s - Sesion: %s", file_type, session_id)
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

        logger.info("[DOWNLOAD] %s - Sesion: %s", file_type, session_id)
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[ERROR] Descargando archivo: %s - Sesion: %s", exc, session_id)
        raise HTTPException(status_code=500, detail="Error al descargar archivo") from exc


@app.get("/health")
async def health():
    """
    Verifica que la aplicacion este en funcionamiento.
    """
    return {
        "status": "healthy",
        "app": "RPA Doc Generator",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/")
async def root():
    """
    Pagina raiz de la API.
    """
    return {
        "message": "RPA Doc Generator API",
        "version": "1.0.0",
        "docs": "http://localhost:8000/docs",
        "redoc": "http://localhost:8000/redoc",
        "health": "http://localhost:8000/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
    )
