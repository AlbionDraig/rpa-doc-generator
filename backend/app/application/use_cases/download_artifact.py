from pathlib import Path


def _first_match(output_dir, pattern):
    matches = list(output_dir.glob(pattern))
    return matches[0] if matches else None


def resolve_download_file(output_dir: Path, file_type: str):
    file_map = {
        "sdd": lambda: _first_match(output_dir, "SDD_*.md"),
        "sdd_word": lambda: _first_match(output_dir, "SDD_*.docx"),
        "sdd_pdf": lambda: _first_match(output_dir, "SDD_*.pdf"),
        "calidad": lambda: _first_match(output_dir, "Calidad_*.md"),
        "calidad_word": lambda: _first_match(output_dir, "Calidad_*.docx"),
        "calidad_pdf": lambda: _first_match(output_dir, "Calidad_*.pdf"),
        "flujo_svg": lambda: output_dir / "flujo_taskbots.svg",
    }

    resolver = file_map.get(file_type)
    if resolver is None:
        return None
    return resolver()
