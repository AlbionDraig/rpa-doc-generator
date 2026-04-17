from datetime import datetime
from pathlib import Path
import shutil

from app.generator.pdf_generator import generate_quality_pdf
from app.generator.sdd_generator import generate_quality_file
from app.generator.word_generator import generate_quality_word
from app.ingestion.extractor import extract_project
from app.ingestion.uploader import save_file
from app.parser.project_parser import parse_project


def run_generate_quality(file, settings, logger):
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = settings.output_dir / session_id
    zip_path = None
    project_path = None

    try:
        logger.info("[QUALITY-START] Procesando archivo: %s - Sesion: %s", file.filename, session_id)
        zip_path = save_file(file)
        project_path = extract_project(zip_path)
        project_data = parse_project(project_path)

        output_dir.mkdir(parents=True, exist_ok=True)

        quality_file = output_dir / f"Calidad_{project_data['name']}.md"
        generate_quality_file(project_data, str(quality_file))
        quality_md_content = quality_file.read_text(encoding="utf-8")

        quality_word_file = output_dir / f"Calidad_{project_data['name']}.docx"
        generate_quality_word(project_data, str(quality_word_file), md_content=quality_md_content)

        quality_pdf_file = output_dir / f"Calidad_{project_data['name']}.pdf"
        generate_quality_pdf(quality_md_content, str(quality_pdf_file), project_data["name"])

        logger.info("[QUALITY-COMPLETE] Reporte generado - Sesion: %s", session_id)
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
        if project_path:
            shutil.rmtree(Path(project_path), ignore_errors=True)
        if zip_path:
            Path(zip_path).unlink(missing_ok=True)
