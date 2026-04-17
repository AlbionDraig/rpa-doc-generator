from datetime import datetime
from pathlib import Path
import shutil
import time

from app.analysis.flow_builder import build_flow
from app.analysis.tree_builder import build_tree
from app.generator.diagram_generator import convert_svg_to_png, generate_flow_svg
from app.generator.pdf_generator import generate_sdd_pdf
from app.generator.sdd_generator import generate_sdd, generate_sdd_file
from app.generator.word_generator import generate_sdd_word
from app.ingestion.extractor import extract_project
from app.ingestion.uploader import save_file
from app.observability import bind_logger, bind_session, reset_session
from app.parser.project_parser import parse_project


def run_generate_sdd(file, settings, logger):
    """Generate SDD (Software Design Document) for an RPA project.
    
    Orchestrates the complete pipeline:
    1. Save uploaded ZIP file
    2. Extract project contents
    3. Parse project structure (taskbots, nodes, variables, metadata)
    4. Build task dependency flow
    5. Generate file tree
    6. Create SVG flow diagram and convert to PNG
    7. Generate SDD in Markdown, DOCX, and PDF formats
    
    Args:
        file: UploadFile object from FastAPI (ZIP file).
        settings: AppSettings instance with runtime configuration.
        logger: Logger instance for tracking progress.
    
    Returns:
        Dictionary with status and generated artifacts.
    
    Raises:
        ValueError: If file is not a ZIP or exceeds size limits.
    """
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = settings.output_dir / session_id
    zip_path = None
    project_path = None
    started_at = time.perf_counter()
    session_token = bind_session(session_id)
    logger = bind_logger(logger, session_id=session_id)

    try:
        logger.info("[START] Procesando archivo: %s - Sesion: %s", file.filename, session_id)
        logger.info("[1/7] Guardando archivo...")
        zip_path = save_file(file, settings=settings)

        logger.info("[2/7] Extrayendo contenido...")
        project_path = extract_project(zip_path, settings=settings)

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

        flow_png_file = output_dir / "flujo_taskbots.png"
        convert_svg_to_png(str(flow_svg_file), str(flow_png_file))

        flow_visual = "\n".join(
            [
                "![Flujo principal entre taskbots](flujo_taskbots.svg)",
                "",
                "_La imagen muestra entrypoints, direccion de invocacion y el contrato resumido por flecha cuando aplica._",
            ]
        )

        logger.info("[7/7] Generando documentacion...")
        sdd = generate_sdd(project_data, tree, flow, flow_visual, settings=settings)

        sdd_file = output_dir / f"SDD_{project_data['name']}.md"
        generate_sdd_file(project_data, tree, str(sdd_file), flow, flow_visual, settings=settings)

        sdd_word_file = output_dir / f"SDD_{project_data['name']}.docx"
        generate_sdd_word(project_data, tree, str(sdd_word_file), flow, str(flow_png_file))

        sdd_pdf_file = output_dir / f"SDD_{project_data['name']}.pdf"
        generate_sdd_pdf(sdd, str(sdd_pdf_file), project_data["name"], str(flow_png_file))

        if flow_png_file.exists():
            flow_png_file.unlink()

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "[COMPLETE] Procesamiento finalizado - Sesion: %s - Proyecto: %s - DuracionMs: %s",
            session_id,
            project_data["name"],
            duration_ms,
        )
        return {
            "status": "success",
            "session_id": session_id,
            "proyecto": project_data["name"],
            "archivos_salida": {
                "sdd_path": str(sdd_file),
                "sdd_word_path": str(sdd_word_file),
                "sdd_pdf_path": str(sdd_pdf_file),
                "flujo_svg_path": str(flow_svg_file),
            },
            "output_directory": str(output_dir),
        }
    finally:
        reset_session(session_token)
        if project_path:
            shutil.rmtree(Path(project_path), ignore_errors=True)
        if zip_path:
            Path(zip_path).unlink(missing_ok=True)
