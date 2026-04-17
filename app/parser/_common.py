import json
import os
import re
from pathlib import Path
from urllib.parse import unquote

TASKBOT_CONTENT_TYPE = "application/vnd.aa.taskbot"
METADATA_DIR_FRAGMENT = "metadata"
SENSITIVE_FIELD_PATTERN = re.compile(
    r"(password|passwd|pwd|token|secret|api[_-]?key|authorization)",
    re.IGNORECASE,
)
URL_CREDENTIAL_PATTERN = re.compile(
    r"([?&](?:user|username|password|pwd)=)([^&]+)",
    re.IGNORECASE,
)
WINDOWS_USER_PATH_PATTERN = re.compile(r"([A-Za-z]:\\Users\\)([^\\]+)")
WINDOWS_PATH_PATTERN = re.compile(r"^[A-Za-z]:\\")
TASKBOT_HINT_KEYS = {"nodes", "variables", "packages", "properties"}
UI_NOISE_KEYS = {
    "blob",
    "outerHTML",
    "innerHTML",
    "criteria",
    "capture",
    "thumbnailMetadataPath",
    "screenshotMetadataPath",
}
HEADER_COMMENT_PREFIXES = {
    "developer": "developer",
    "fecha": "date",
    "date": "date",
    "descripcion": "description",
    "description": "description",
}


def sanitize_text(value, field_name=None):
    if value is None:
        return ""

    if isinstance(value, bool):
        return str(value).lower()

    text = str(value)
    if not text:
        return ""

    if field_name and SENSITIVE_FIELD_PATTERN.search(field_name):
        return "<redacted>"

    text = URL_CREDENTIAL_PATTERN.sub(r"\1<redacted>", text)
    text = WINDOWS_USER_PATH_PATTERN.sub(r"\1<user>", text)

    if text.startswith("jdbc:"):
        return _sanitize_jdbc_url(text)

    if text.startswith("file://"):
        file_target = text[len("file://") :]
        return f"file://{_sanitize_local_path(file_target)}"

    if WINDOWS_PATH_PATTERN.match(text):
        return _sanitize_local_path(text)

    if SENSITIVE_FIELD_PATTERN.search(text):
        return "<redacted>"

    return text


def _sanitize_jdbc_url(text):
    return URL_CREDENTIAL_PATTERN.sub(r"\1<redacted>", text)


def _sanitize_local_path(path_text):
    return WINDOWS_USER_PATH_PATTERN.sub(r"\1<user>", path_text)


def _normalize_path_text(path_text):
    return str(path_text).replace("/", os.sep).replace("\\", os.sep)


def _normalize_repository_path(repository_path):
    if not repository_path:
        return ""

    normalized = repository_path
    if normalized.startswith("repository:///"):
        normalized = normalized[len("repository:///") :]
    normalized = unquote(normalized)
    return _normalize_path_text(normalized)


def _load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def _get_attribute(node, name):
    for attribute in node.get("attributes", []):
        if attribute.get("name") == name:
            return attribute.get("value")
    return None


def _extract_value_literal(value):
    if value is None:
        return ""

    if isinstance(value, dict):
        for key in ("string", "expression", "number", "boolean", "variableName", "sessionName"):
            if key in value:
                return value[key]

        if "taskbotFile" in value:
            return value["taskbotFile"].get("string") or value["taskbotFile"].get("expression") or ""

        if "dictionary" in value:
            return ", ".join(item.get("key", "") for item in value["dictionary"] if isinstance(item, dict))

    return value


def _get_attribute_string(node, name):
    return sanitize_text(_extract_value_literal(_get_attribute(node, name)), field_name=name)


def _flatten_attribute_values(value, parent_key=None):
    if value is None:
        return []

    if isinstance(value, dict):
        flattened = []
        for key, nested_value in value.items():
            if key in UI_NOISE_KEYS:
                continue
            if key in {"string", "expression"} and nested_value:
                flattened.append(str(nested_value))
            else:
                flattened.extend(_flatten_attribute_values(nested_value, parent_key=key))
        return flattened

    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten_attribute_values(item, parent_key=parent_key))
        return flattened

    if isinstance(value, str):
        return [] if len(value) > 500 else [value]

    return [str(value)]


def _extract_comment_text(node):
    if str(node.get("commandName", "")).lower() != "comment":
        return ""
    return sanitize_text(_get_attribute_string(node, "comment"))


def _is_header_comment(comment_text):
    normalized = comment_text.lower()
    return any(normalized.startswith(f"{prefix}:") for prefix in HEADER_COMMENT_PREFIXES)


def _sanitize_mapping(mapping):
    if not isinstance(mapping, dict):
        return {}

    sanitized = {}
    for key, value in mapping.items():
        if isinstance(value, dict):
            sanitized[key] = _sanitize_mapping(value)
        elif isinstance(value, list):
            sanitized[key] = [
                _sanitize_mapping(item) if isinstance(item, dict) else sanitize_text(item, field_name=key)
                for item in value
            ]
        else:
            sanitized[key] = sanitize_text(value, field_name=key)

    return sanitized


def _sanitize_packages(packages):
    sanitized = []
    for package in packages:
        if not isinstance(package, dict):
            continue
        sanitized.append(
            {
                "name": sanitize_text(package.get("name", "")),
                "version": sanitize_text(package.get("version", "")),
            }
        )
    return sanitized


def _sanitize_triggers(triggers):
    sanitized = []
    for trigger in triggers:
        if not isinstance(trigger, dict):
            continue
        sanitized.append(_sanitize_mapping(trigger))
    return sanitized


def _should_skip_file(file_path):
    path_parts = {part.lower() for part in file_path.parts}
    if any(METADATA_DIR_FRAGMENT in part for part in path_parts):
        return True

    if file_path.suffix.lower() in {".jar", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".class"}:
        return True

    return False


def _looks_like_taskbot(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False

    return isinstance(data, dict) and TASKBOT_HINT_KEYS.issubset(data.keys())


def _load_manifest(project_root, logger):
    manifest_path = Path(project_root) / "manifest.json"
    if not manifest_path.exists():
        return {}

    try:
        with open(manifest_path, "r", encoding="utf-8") as file_obj:
            return json.load(file_obj)
    except json.JSONDecodeError as exc:
        logger.warning("No fue posible parsear manifest.json: %s", exc)
        return {}
