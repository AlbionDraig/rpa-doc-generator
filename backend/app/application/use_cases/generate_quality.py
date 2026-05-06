from datetime import datetime
from pathlib import Path
import shutil
import time

from app.generator.pdf_generator import generate_quality_pdf
from app.generator.sdd_generator import generate_quality_file
from app.generator.word_generator import generate_quality_word
from app.ingestion.extractor import extract_project
from app.ingestion.uploader import save_file
from app.observability import bind_logger, bind_session, reset_session
from app.parser.project_parser import parse_project


def run_generate_quality(file, settings, logger):
    """Generate quality/code review report for an RPA project.
    
    Analyzes code structure and generates findings with prioritization and remediation plan.
    Creates Markdown, DOCX, and PDF quality reports.
    
    Args:
        file: UploadFile object from FastAPI (ZIP file containing the bot).
        settings: AppSettings instance with runtime configuration.
        logger: Logger instance for tracking progress.
    
    Returns:
        Dictionary with generated report paths and session metadata.
    
    Raises:
        ValueError: If file validation or extraction fails.
    """
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = settings.output_dir / session_id
    zip_path = None
    project_path = None
    started_at = time.perf_counter()
    session_token = bind_session(session_id)
    logger = bind_logger(logger, session_id=session_id)

    try:
        logger.info("[QUALITY-START] Procesando archivo: %s - Sesion: %s", file.filename, session_id)
        zip_path = save_file(file, settings=settings)
        project_path = extract_project(zip_path, settings=settings)
        project_data = parse_project(project_path)

        output_dir.mkdir(parents=True, exist_ok=True)

        quality_file = output_dir / f"Calidad_{project_data['name']}.md"
        generate_quality_file(project_data, str(quality_file), settings=settings)
        quality_md_content = quality_file.read_text(encoding="utf-8")

        quality_word_file = output_dir / f"Calidad_{project_data['name']}.docx"
        generate_quality_word(project_data, str(quality_word_file), md_content=quality_md_content)

        quality_pdf_file = output_dir / f"Calidad_{project_data['name']}.pdf"
        generate_quality_pdf(quality_md_content, str(quality_pdf_file), project_data["name"])

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "[QUALITY-COMPLETE] Reporte generado - Sesion: %s - Proyecto: %s - DuracionMs: %s",
            session_id,
            project_data["name"],
            duration_ms,
        )
        return {
            "status": "success",
            "session_id": session_id,
            "proyecto": project_data["name"],
            "archivos_salida": {
                "calidad_path": str(quality_file),
                "calidad_word_path": str(quality_word_file),
                "calidad_pdf_path": str(quality_pdf_file),
            },
            "output_directory": str(output_dir),
        }
    finally:
        reset_session(session_token)
        if project_path:
            shutil.rmtree(Path(project_path), ignore_errors=True)
        if zip_path:
            Path(zip_path).unlink(missing_ok=True)
