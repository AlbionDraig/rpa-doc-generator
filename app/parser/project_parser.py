import json
import logging
import os
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

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


def parse_project(path):
    """
    Parsea un proyecto exportado de Automation Anywhere 360.

    El flujo prioriza el archivo `manifest.json` para descubrir taskbots
    y dependencias reales. Cuando no existe, intenta identificar taskbots
    por su estructura JSON.
    """
    project_root = Path(path)
    if not project_root.exists():
        logger.error("Ruta no encontrada: %s", project_root)
        raise FileNotFoundError(f"La ruta {project_root} no existe")

    manifest = _load_manifest(project_root)
    task_entries = _discover_task_entries(project_root, manifest)
    tasks = []

    for entry in task_entries:
        try:
            task_info = _parse_task_entry(project_root, entry)
        except Exception as exc:
            logger.warning("Error parseando taskbot %s: %s", entry.get("path"), exc)
            continue

        if task_info:
            tasks.append(task_info)

    tasks = _mark_entrypoints(tasks)
    tasks = sorted(
        tasks,
        key=lambda task: (
            0 if task.get("is_entrypoint") else 1,
            0 if task.get("role") == "main" else 1,
            task.get("name", "").lower(),
        ),
    )
    manifest_summary = _build_manifest_summary(manifest)
    project_packages = _collect_project_packages(manifest_summary, tasks)
    external_systems = _collect_project_systems(tasks)

    result = {
        "name": project_root.name,
        "path": str(project_root),
        "tasks": tasks,
        "task_count": len(tasks),
        "metadata": {
            "description": _select_project_description(tasks),
            "manifest": manifest_summary,
            "entrypoints": [task["name"] for task in tasks if task.get("is_entrypoint")],
        },
        "files": _build_file_summary(project_root, manifest, tasks),
        "packages": project_packages,
        "systems": external_systems,
    }

    logger.info(
        "Proyecto AA360 parseado: %s con %s taskbots",
        result["name"],
        result["task_count"],
    )
    return result


def _load_manifest(project_root):
    manifest_path = project_root / "manifest.json"
    if not manifest_path.exists():
        return {}

    try:
        with open(manifest_path, "r", encoding="utf-8") as file_obj:
            return json.load(file_obj)
    except json.JSONDecodeError as exc:
        logger.warning("No fue posible parsear manifest.json: %s", exc)
        return {}


def _discover_task_entries(project_root, manifest):
    entries = []

    manifest_files = manifest.get("files", []) if isinstance(manifest, dict) else []
    for entry in manifest_files:
        if entry.get("contentType") != TASKBOT_CONTENT_TYPE:
            continue

        relative_path = entry.get("path")
        if not relative_path:
            continue

        file_path = project_root / Path(relative_path)
        if file_path.exists():
            entries.append(entry)

    if entries:
        return entries

    for file_path in project_root.rglob("*"):
        if not file_path.is_file():
            continue
        if _should_skip_file(file_path):
            continue

        relative_path = str(file_path.relative_to(project_root))
        if _looks_like_taskbot(file_path):
            entries.append(
                {
                    "path": relative_path,
                    "manualDependencies": [],
                    "scannedDependencies": [],
                    "contentType": TASKBOT_CONTENT_TYPE,
                }
            )

    return entries


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


def _parse_task_entry(project_root, entry):
    relative_path = entry.get("path", "")
    task_path = project_root / Path(relative_path)
    if not task_path.exists():
        return None

    data = _load_json(task_path)
    if not isinstance(data, dict):
        return None

    if TASKBOT_HINT_KEYS.issubset(data.keys()):
        return _parse_taskbot(task_path, project_root, data, entry)

    if task_path.suffix.lower() == ".xml":
        return _parse_xml_file(str(task_path), relative_path)

    if task_path.suffix.lower() == ".json":
        return _parse_json_file(str(task_path), relative_path)

    return None


def _parse_taskbot(task_path, project_root, data, manifest_entry):
    relative_path = str(task_path.relative_to(project_root))
    header = _extract_header_metadata(data.get("nodes", []))
    node_analysis = _analyze_nodes(data.get("nodes", []))
    variables = _extract_taskbot_variables(data.get("variables", []))
    dependencies = _merge_dependencies(manifest_entry, node_analysis["task_calls"])
    role = _detect_role(relative_path, task_path.name)

    return {
        "name": task_path.name,
        "path": relative_path,
        "type": "taskbot",
        "role": role,
        "size": task_path.stat().st_size,
        "description": header.get("description", ""),
        "developer": header.get("developer", ""),
        "declared_date": header.get("date", ""),
        "variables": variables,
        "packages": _sanitize_packages(data.get("packages", [])),
        "properties": _sanitize_mapping(data.get("properties", {})),
        "triggers": _sanitize_triggers(data.get("triggers", [])),
        "dependencies": dependencies,
        "task_calls": node_analysis["task_calls"],
        "actions": node_analysis["actions"],
        "node_stats": node_analysis["stats"],
        "error_handling": node_analysis["error_handling"],
        "systems": node_analysis["systems"],
        "comments": node_analysis["comments"],
    }


def _extract_header_metadata(nodes):
    metadata = {}

    for node in nodes[:10]:
        if node.get("commandName") != "Comment":
            continue

        comment = _extract_comment_text(node)
        if not comment:
            continue

        match = re.match(r"^\s*([^:]+)\s*:\s*(.+?)\s*$", comment)
        if not match:
            continue

        key = match.group(1).strip().lower()
        value = sanitize_text(match.group(2).strip(), field_name=key)
        mapped_key = HEADER_COMMENT_PREFIXES.get(key)
        if mapped_key:
            metadata[mapped_key] = value

    return metadata


def _extract_taskbot_variables(variables):
    result = {"input": [], "output": [], "internal": []}

    for variable in variables:
        if not isinstance(variable, dict):
            continue

        default_value = _extract_value_literal(variable.get("defaultValue"))
        variable_info = {
            "name": variable.get("name", "N/A"),
            "type": variable.get("type", "UNKNOWN"),
            "description": sanitize_text(variable.get("description", "")),
            "default": sanitize_text(default_value, field_name=variable.get("name")),
            "read_only": bool(variable.get("readOnly", False)),
            "scope": _infer_variable_scope(variable.get("name", "")),
        }

        if variable.get("input"):
            result["input"].append(variable_info)
        if variable.get("output"):
            result["output"].append(variable_info)
        if not variable.get("input") and not variable.get("output"):
            result["internal"].append(variable_info)

    return result


def _infer_variable_scope(variable_name):
    normalized = (variable_name or "").lower()
    if normalized.startswith("gbl"):
        return "global"
    if normalized.startswith("loc"):
        return "local"
    if normalized.startswith("in"):
        return "input"
    if normalized.startswith("out"):
        return "output"
    return "unspecified"


def _analyze_nodes(nodes):
    analysis = {
        "actions": [],
        "task_calls": [],
        "systems": [],
        "comments": [],
        "stats": {
            "total_nodes": 0,
            "disabled_nodes": 0,
            "decision_nodes": 0,
            "loop_nodes": 0,
            "task_calls": 0,
            "error_handlers": 0,
            "step_groups": 0,
        },
        "error_handling": {
            "has_try": False,
            "has_catch": False,
            "has_finally": False,
        },
    }
    seen_systems = set()

    for node in nodes:
        _visit_node(node, analysis, seen_systems, depth=0)

    return analysis


def _visit_node(node, analysis, seen_systems, depth):
    if not isinstance(node, dict):
        return

    command_name = str(node.get("commandName", ""))
    package_name = str(node.get("packageName", ""))
    normalized_command = command_name.lower()
    normalized_package = package_name.lower()

    analysis["stats"]["total_nodes"] += 1
    if node.get("disabled"):
        analysis["stats"]["disabled_nodes"] += 1
    if normalized_command == "if" or normalized_package == "if":
        analysis["stats"]["decision_nodes"] += 1
    if normalized_command.startswith("loop") or normalized_package == "loop":
        analysis["stats"]["loop_nodes"] += 1
    if normalized_command == "runtask":
        analysis["stats"]["task_calls"] += 1
    if normalized_package == "errorhandler" or normalized_command in {"try", "catch", "finally"}:
        analysis["stats"]["error_handlers"] += 1
    if normalized_command == "step":
        analysis["stats"]["step_groups"] += 1

    if normalized_command == "try":
        analysis["error_handling"]["has_try"] = True
    if normalized_command == "catch":
        analysis["error_handling"]["has_catch"] = True
    if normalized_command == "finally":
        analysis["error_handling"]["has_finally"] = True

    comment_text = _extract_comment_text(node)
    if comment_text and not _is_header_comment(comment_text):
        analysis["comments"].append(comment_text)

    summary = _summarize_node(node, depth)
    if summary and _should_keep_summary(node, depth):
        analysis["actions"].append(summary)

    if normalized_command == "runtask":
        task_call = _extract_task_call(node)
        if task_call:
            analysis["task_calls"].append(task_call)

    for system in _extract_systems_from_node(node):
        signature = (system["type"], system["value"])
        if signature not in seen_systems:
            seen_systems.add(signature)
            analysis["systems"].append(system)

    for child in node.get("children", []):
        _visit_node(child, analysis, seen_systems, depth + 1)

    for branch in node.get("branches", []):
        _visit_node(branch, analysis, seen_systems, depth + 1)


def _should_keep_summary(node, depth):
    if depth == 0:
        return True

    command = str(node.get("commandName", "")).lower()
    return command in {
        "step",
        "runtask",
        "if",
        "try",
        "catch",
        "finally",
        "openbrowser",
        "connect",
        "exporttodatatable",
        "insertupdatedelete",
        "logtofile",
        "capturewindow",
    }


def _summarize_node(node, depth):
    command = str(node.get("commandName", ""))
    package = str(node.get("packageName", ""))
    normalized_command = command.lower()
    normalized_package = package.lower()

    if normalized_command == "comment":
        text = _extract_comment_text(node)
        if text and not _is_header_comment(text):
            return text
        return None

    if normalized_command == "step":
        title = _get_attribute_string(node, "title")
        if title:
            return f"Grupo: {title}"
        return "Grupo de pasos"

    if normalized_command == "runtask":
        task_call = _extract_task_call(node)
        if not task_call:
            return "Invoca una subtask"
        return (
            f"Invoca subtask {task_call['target_name']} "
            f"({len(task_call['inputs'])} entradas, {len(task_call['outputs'])} salidas)"
        )

    if normalized_command == "if":
        return f"Decision condicional en {package or 'If'}"

    if normalized_command.startswith("loop") or normalized_package == "loop":
        return "Iteracion o reintento"

    if normalized_command == "try":
        return "Inicio de bloque de manejo de errores"
    if normalized_command == "catch":
        return "Captura y trata errores"
    if normalized_command == "finally":
        return "Ejecuta acciones de cierre"

    if normalized_package == "database":
        if normalized_command == "connect":
            return "Abre conexion a base de datos"
        if normalized_command == "exporttodatatable":
            return "Consulta registros desde base de datos"
        if normalized_command == "insertupdatedelete":
            return "Actualiza informacion en base de datos"
        if normalized_command == "disconnect":
            return "Cierra conexion a base de datos"

    if normalized_package == "browser":
        if normalized_command == "openbrowser":
            return "Abre el navegador y navega al sitio objetivo"
        if normalized_command == "close":
            return "Cierra el navegador o una pestana"

    if normalized_package == "logtofile":
        return "Registra trazas en archivo de log"

    if normalized_package == "recorder":
        return "Interactua con la interfaz web capturada"

    if normalized_package == "screen" and normalized_command == "capturewindow":
        return "Captura evidencia de pantalla"

    if depth == 0 and (command or package):
        return f"Ejecuta {package or 'comando'}::{command}"

    return None


def _extract_task_call(node):
    taskbot_attribute = _get_attribute(node, "taskbot")
    if not taskbot_attribute:
        return None

    taskbot_file = (
        taskbot_attribute.get("taskbotFile", {}).get("string")
        or taskbot_attribute.get("taskbotFile", {}).get("expression")
        or ""
    )
    target_path = _normalize_repository_path(taskbot_file)

    input_dictionary = taskbot_attribute.get("taskbotInput", {}).get("dictionary", [])
    return_dictionary = node.get("returnTo", {}).get("dictionary", [])

    return {
        "target_path": target_path,
        "target_name": Path(target_path).name if target_path else "subtask",
        "inputs": [
            {
                "name": item.get("key", "N/A"),
                "value": sanitize_text(_extract_value_literal(item.get("value")), field_name=item.get("key")),
            }
            for item in input_dictionary
            if isinstance(item, dict)
        ],
        "outputs": [
            {
                "name": item.get("key", "N/A"),
                "value": sanitize_text(item.get("value", {}).get("variableName", ""), field_name=item.get("key")),
            }
            for item in return_dictionary
            if isinstance(item, dict)
        ],
    }


def _merge_dependencies(manifest_entry, task_calls):
    dependencies = []
    seen_paths = set()

    for task_call in task_calls:
        dependency_path = _normalize_path_text(task_call.get("target_path", ""))
        if not dependency_path or dependency_path in seen_paths:
            continue
        seen_paths.add(dependency_path)
        dependencies.append(
            {
                "path": dependency_path,
                "name": Path(dependency_path).name,
                "type": "runTask",
            }
        )

    for dependency_type, key in (("manual", "manualDependencies"), ("scanned", "scannedDependencies")):
        for dependency_path in manifest_entry.get(key, []) or []:
            normalized_path = _normalize_path_text(dependency_path)
            if not normalized_path or normalized_path in seen_paths:
                continue
            seen_paths.add(normalized_path)
            dependencies.append(
                {
                    "path": normalized_path,
                    "name": Path(normalized_path).name,
                    "type": dependency_type,
                }
            )

    return dependencies


def _detect_role(relative_path, task_name):
    normalized_path = relative_path.replace("/", "\\").lower()
    if task_name.lower() == "main":
        return "main"
    if "\\tareas\\" in normalized_path or "\\subtasks\\" in normalized_path:
        return "subtask"
    return "taskbot"


def _mark_entrypoints(tasks):
    if not tasks:
        return tasks

    inbound = Counter()
    task_paths = {task["path"] for task in tasks}

    for task in tasks:
        for dependency in task.get("dependencies", []):
            dependency_path = _normalize_path_text(dependency.get("path", ""))
            if dependency_path in task_paths:
                inbound[dependency_path] += 1

    for task in tasks:
        task["is_entrypoint"] = (
            task.get("role") == "main"
            or inbound.get(task["path"], 0) == 0
        )

    return tasks


def _build_manifest_summary(manifest):
    if not manifest:
        return {}

    files = manifest.get("files", [])
    packages = manifest.get("packages", [])
    taskbot_files = [
        file_info.get("path", "")
        for file_info in files
        if file_info.get("contentType") == TASKBOT_CONTENT_TYPE
    ]

    return {
        "taskbot_files": taskbot_files,
        "package_count": len(packages),
        "packages": _sanitize_packages(packages),
        "file_count": len(files),
    }


def _collect_project_packages(manifest_summary, tasks):
    packages_by_name = {}

    for package in manifest_summary.get("packages", []):
        packages_by_name[package["name"]] = package

    for task in tasks:
        for package in task.get("packages", []):
            packages_by_name[package["name"]] = package

    return sorted(packages_by_name.values(), key=lambda item: item["name"].lower())


def _collect_project_systems(tasks):
    systems = []
    seen = set()

    for task in tasks:
        for system in task.get("systems", []):
            signature = (system["type"], system["value"])
            if signature in seen:
                continue
            seen.add(signature)
            systems.append(system)

    return sorted(systems, key=lambda item: (item["type"], item["value"]))


def _select_project_description(tasks):
    for task in tasks:
        description = task.get("description")
        if description:
            return description
    return "Documentacion auto-generada del bot RPA"


def _build_file_summary(project_root, manifest, tasks):
    xml_count = 0
    json_count = 1 if manifest else 0
    other_count = 0
    task_paths = {task["path"] for task in tasks}

    for file_path in project_root.rglob("*"):
        if not file_path.is_file() or _should_skip_file(file_path):
            continue

        if file_path.name == "manifest.json":
            continue

        relative_path = str(file_path.relative_to(project_root))
        if file_path.suffix.lower() == ".xml":
            xml_count += 1
        elif file_path.suffix.lower() == ".json":
            json_count += 1
        elif relative_path not in task_paths:
            other_count += 1

    return {
        "xml_count": xml_count,
        "json_count": json_count,
        "taskbot_count": len(tasks),
        "manifest_count": 1 if manifest else 0,
        "other_count": other_count,
    }


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


def _extract_systems_from_node(node):
    systems = []
    command = str(node.get("commandName", "")).lower()
    package = str(node.get("packageName", "")).lower()

    for attribute in node.get("attributes", []):
        if not isinstance(attribute, dict):
            continue

        attribute_name = str(attribute.get("name", ""))
        if attribute_name.lower() in {"query", "uiobject", "windowtitle"}:
            continue

        for value in _flatten_attribute_values(attribute.get("value")):
            if not value:
                continue

            if value.startswith("jdbc:"):
                systems.append(
                    {
                        "type": "database",
                        "value": sanitize_text(value, field_name=attribute_name),
                        "source": f"{package or 'command'}::{command or attribute_name}",
                    }
                )
            elif value.startswith("http://") or value.startswith("https://"):
                systems.append(
                    {
                        "type": "url",
                        "value": sanitize_text(value, field_name=attribute_name),
                        "source": f"{package or 'command'}::{command or attribute_name}",
                    }
                )
            elif value.startswith("file://") or WINDOWS_PATH_PATTERN.match(value):
                systems.append(
                    {
                        "type": "file",
                        "value": sanitize_text(value, field_name=attribute_name),
                        "source": f"{package or 'command'}::{command or attribute_name}",
                    }
                )

    if package == "database" and command in {"exporttodatatable", "insertupdatedelete"}:
        systems.append({"type": "database", "value": "Operacion SQL", "source": f"{package}::{command}"})

    return systems


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


def _get_attribute(node, name):
    for attribute in node.get("attributes", []):
        if attribute.get("name") == name:
            return attribute.get("value")
    return None


def _get_attribute_string(node, name):
    return sanitize_text(_extract_value_literal(_get_attribute(node, name)), field_name=name)


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


def _normalize_repository_path(repository_path):
    if not repository_path:
        return ""

    normalized = repository_path
    if normalized.startswith("repository:///"):
        normalized = normalized[len("repository:///") :]
    normalized = unquote(normalized)
    return _normalize_path_text(normalized)


def _normalize_path_text(path_text):
    return str(path_text).replace("/", os.sep).replace("\\", os.sep)


def _load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def _parse_xml_file(file_path, relative_path):
    """Extrae informacion de un archivo XML incluyendo detalles generales."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        variables = _extract_variables_from_xml(root)
        actions = _extract_actions_from_xml(root)

        return {
            "name": os.path.basename(file_path),
            "path": relative_path,
            "type": "xml",
            "description": sanitize_text(root.attrib.get("Description", root.attrib.get("description", ""))),
            "attributes": _sanitize_mapping(root.attrib),
            "size": os.path.getsize(file_path),
            "variables": {
                "input": variables["input"],
                "output": variables["output"],
                "internal": [],
            },
            "actions": actions,
            "dependencies": [],
            "systems": [],
            "node_stats": {"total_nodes": len(list(root.iter()))},
            "error_handling": {"has_try": False, "has_catch": False, "has_finally": False},
            "task_calls": [],
            "packages": [],
            "properties": {},
            "triggers": [],
            "comments": [],
            "role": "document",
            "is_entrypoint": False,
        }
    except Exception as exc:
        logger.debug("Error parseando XML %s: %s", file_path, exc)
        return None


def _parse_json_file(file_path, relative_path):
    """Extrae informacion de un JSON generico cuando no es taskbot."""
    try:
        with open(file_path, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)

        description = ""
        if isinstance(data, dict):
            description = data.get("description", data.get("Description", ""))

        variables = _extract_variables_from_json(data)
        return {
            "name": os.path.basename(file_path),
            "path": relative_path,
            "type": "json",
            "description": sanitize_text(description),
            "attributes": {},
            "size": os.path.getsize(file_path),
            "variables": {
                "input": variables["input"],
                "output": variables["output"],
                "internal": [],
            },
            "actions": [],
            "dependencies": [],
            "systems": [],
            "node_stats": {"total_nodes": len(data) if isinstance(data, (dict, list)) else 0},
            "error_handling": {"has_try": False, "has_catch": False, "has_finally": False},
            "task_calls": [],
            "packages": [],
            "properties": {},
            "triggers": [],
            "comments": [],
            "role": "document",
            "is_entrypoint": False,
        }
    except Exception as exc:
        logger.debug("Error parseando JSON %s: %s", file_path, exc)
        return None


def _extract_variables_from_xml(root):
    variables = {"input": [], "output": []}

    try:
        for element in root.iter():
            tag = element.tag.lower()
            if "input" in tag or "parameter" in tag:
                variables["input"].append(
                    {
                        "name": element.attrib.get("Name", element.attrib.get("name", "Unknown")),
                        "type": element.attrib.get("Type", element.attrib.get("type", "String")),
                        "default": sanitize_text(element.attrib.get("Value", element.attrib.get("value", ""))),
                        "description": "",
                        "read_only": False,
                        "scope": "input",
                    }
                )
            if "output" in tag or "return" in tag:
                variables["output"].append(
                    {
                        "name": element.attrib.get("Name", element.attrib.get("name", "Unknown")),
                        "type": element.attrib.get("Type", element.attrib.get("type", "String")),
                        "default": sanitize_text(element.attrib.get("Value", element.attrib.get("value", ""))),
                        "description": "",
                        "read_only": False,
                        "scope": "output",
                    }
                )
    except Exception as exc:
        logger.debug("Error extrayendo variables XML: %s", exc)

    return variables


def _extract_variables_from_json(data):
    variables = {"input": [], "output": []}

    try:
        if not isinstance(data, dict):
            return variables

        for key, value in data.items():
            normalized_key = key.lower()
            if not isinstance(value, dict):
                continue

            if "input" in normalized_key:
                for variable_name, variable_value in value.items():
                    variables["input"].append(
                        {
                            "name": variable_name,
                            "type": type(variable_value).__name__,
                            "default": sanitize_text(variable_value, field_name=variable_name),
                            "description": "",
                            "read_only": False,
                            "scope": "input",
                        }
                    )
            elif "output" in normalized_key:
                for variable_name, variable_value in value.items():
                    variables["output"].append(
                        {
                            "name": variable_name,
                            "type": type(variable_value).__name__,
                            "default": sanitize_text(variable_value, field_name=variable_name),
                            "description": "",
                            "read_only": False,
                            "scope": "output",
                        }
                    )
    except Exception as exc:
        logger.debug("Error extrayendo variables JSON: %s", exc)

    return variables


def _extract_actions_from_xml(root):
    actions = []

    try:
        for element in root.iter():
            tag = element.tag.lower()
            if "action" in tag or "task" in tag or "step" in tag:
                actions.append(
                    sanitize_text(
                        element.attrib.get("Description")
                        or element.attrib.get("description")
                        or element.attrib.get("Name")
                        or element.attrib.get("name")
                        or element.tag
                    )
                )
    except Exception as exc:
        logger.debug("Error extrayendo acciones XML: %s", exc)

    return actions
