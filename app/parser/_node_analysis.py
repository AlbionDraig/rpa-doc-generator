from pathlib import Path
import re

from app.parser._common import (
    HEADER_COMMENT_PREFIXES,
    UI_NOISE_KEYS,
    WINDOWS_PATH_PATTERN,
    _extract_comment_text,
    _extract_value_literal,
    _flatten_attribute_values,
    _get_attribute,
    _get_attribute_string,
    _is_header_comment,
    _normalize_repository_path,
    sanitize_text,
)


def extract_header_metadata(nodes):
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


def extract_taskbot_variables(variables, infer_variable_scope):
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
            "scope": infer_variable_scope(variable.get("name", "")),
        }

        if variable.get("input"):
            result["input"].append(variable_info)
        if variable.get("output"):
            result["output"].append(variable_info)
        if not variable.get("input") and not variable.get("output"):
            result["internal"].append(variable_info)

    return result


def analyze_nodes(nodes, extract_task_call, summarize_node, should_keep_summary):
    analysis = {
        "actions": [],
        "task_calls": [],
        "systems": [],
        "credentials": [],
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
        visit_node(node, analysis, seen_systems, 0, extract_task_call, summarize_node, should_keep_summary)

    return analysis


def visit_node(node, analysis, seen_systems, depth, extract_task_call, summarize_node, should_keep_summary):
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

    summary = summarize_node(node, depth)
    if summary and should_keep_summary(node, depth):
        analysis["actions"].append(summary)

    if normalized_command == "runtask":
        task_call = extract_task_call(node)
        if task_call:
            analysis["task_calls"].append(task_call)

    for system in extract_systems_from_node(node):
        signature = (system["type"], system["value"])
        if signature not in seen_systems:
            seen_systems.add(signature)
            analysis["systems"].append(system)

    credential = extract_credential_from_node(node)
    if credential:
        analysis["credentials"].append(credential)

    for child in node.get("children", []):
        visit_node(child, analysis, seen_systems, depth + 1, extract_task_call, summarize_node, should_keep_summary)

    for branch in node.get("branches", []):
        visit_node(branch, analysis, seen_systems, depth + 1, extract_task_call, summarize_node, should_keep_summary)


def should_keep_summary(node, depth):
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


def summarize_node(node, depth, extract_task_call):
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
        task_call = extract_task_call(node)
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


def extract_task_call(node):
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


def extract_credential_from_node(node):
    command = str(node.get("commandName", "")).lower()
    package = str(node.get("packageName", "")).lower()

    if "credential" not in package:
        return None

    credential_name = ""
    attribute_name = ""
    vault_name = ""

    for attr in node.get("attributes", []):
        if not isinstance(attr, dict):
            continue
        attr_name = str(attr.get("name", "")).lower()
        attr_value = _extract_value_literal(attr.get("value"))
        attr_str = str(attr_value).strip() if attr_value else ""

        if attr_name in {"credentialname", "credential", "name"}:
            credential_name = attr_str
        elif attr_name in {"attributename", "attribute"}:
            attribute_name = attr_str
        elif attr_name in {"lockername", "locker", "vault", "vaultname"}:
            vault_name = attr_str

    if not credential_name:
        return None

    return {
        "credential_name": credential_name,
        "attribute": attribute_name,
        "vault": vault_name,
        "source": f"{package}::{command}",
    }


def extract_systems_from_node(node):
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
