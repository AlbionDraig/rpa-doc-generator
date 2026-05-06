import logging
import os

logger = logging.getLogger(__name__)

EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
EXCLUDED_EXTENSIONS = {".jar", ".class", ".pyc", ".pyo"}


def build_tree(path, prefix="", include_stats=True):
    """
    Construye una representacion ASCII del arbol de directorios.
    """
    try:
        entries = sorted(os.listdir(path))
        entries = [entry for entry in entries if not should_exclude(entry, path)]

        directories = [entry for entry in entries if os.path.isdir(os.path.join(path, entry))]
        files = [entry for entry in entries if os.path.isfile(os.path.join(path, entry))]
        ordered_entries = directories + files

        lines = []
        for index, entry in enumerate(ordered_entries):
            full_path = os.path.join(path, entry)
            is_last = index == len(ordered_entries) - 1
            connector = "\\-- " if is_last else "|-- "
            next_prefix = "    " if is_last else "|   "

            if os.path.isdir(full_path):
                lines.append(f"{prefix}{connector}📁 {entry}/")
                lines.append(build_tree(full_path, prefix + next_prefix, include_stats))
                continue

            display_name = f"{_detect_file_kind(entry)} {entry}"
            if include_stats:
                display_name += f" ({_format_size(os.path.getsize(full_path))})"
            lines.append(f"{prefix}{connector}{display_name}")

        return "\n".join(line for line in lines if line).rstrip()
    except Exception as exc:
        logger.error("Error construyendo arbol: %s", exc)
        return f"Error: {exc}"


def should_exclude(filename, parent_path=None):
    normalized_name = filename.lower()
    if normalized_name in EXCLUDED_DIRS:
        return True
    if "metadata" in normalized_name:
        return True
    if filename.startswith("."):
        return True

    extension = os.path.splitext(filename)[1].lower()
    if extension in EXCLUDED_EXTENSIONS:
        return True

    full_path = os.path.join(parent_path, filename) if parent_path else filename
    return os.path.isdir(full_path) and normalized_name in EXCLUDED_DIRS


def _detect_file_kind(filename):
    extension = os.path.splitext(filename)[1].lower()
    if extension == ".xml":
        return "📝 [XML]"
    if extension == ".json":
        return "📝 [JSON]"
    if extension == ".csv":
        return "📝 [CSV]"
    if extension in { ".xlsx", ".xls"}:
        return "📊 [EXCEL]"
    if extension == "":
        return "🤖 [BOT]"
    return "📄 [FILE]"


def _format_size(bytes_size):
    size = int(bytes_size)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"
