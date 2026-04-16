from datetime import datetime

from app.analysis.flow_builder import build_flow
from app.analysis.tree_builder import build_tree
from app.generator.diagram_generator import convert_svg_to_png, generate_flow_svg
from app.generator.pdf_generator import generate_sdd_pdf
from app.generator.sdd_generator import generate_sdd, generate_sdd_file
from app.generator.word_generator import generate_sdd_word
from app.ingestion.extractor import extract_project
from app.ingestion.uploader import save_file
from app.parser.project_parser import parse_project


def run_generate_sdd(file, settings, logger):
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = settings.output_dir / session_id

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
    sdd = generate_sdd(project_data, tree, flow, flow_visual)

    sdd_file = output_dir / f"SDD_{project_data['name']}.md"
    generate_sdd_file(project_data, tree, str(sdd_file), flow, flow_visual)

    sdd_word_file = output_dir / f"SDD_{project_data['name']}.docx"
    generate_sdd_word(project_data, tree, str(sdd_word_file), flow, str(flow_png_file))

    sdd_pdf_file = output_dir / f"SDD_{project_data['name']}.pdf"
    generate_sdd_pdf(sdd, str(sdd_pdf_file), project_data["name"], str(flow_png_file))

    if flow_png_file.exists():
        flow_png_file.unlink()

    logger.info("[COMPLETE] Procesamiento finalizado - Sesion: %s", session_id)
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
