import json
import os
import xml.etree.ElementTree as ET

from app.parser._common import _sanitize_mapping, sanitize_text


def parse_xml_file(file_path, relative_path, extract_variables_from_xml, extract_actions_from_xml, logger):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        variables = extract_variables_from_xml(root)
        actions = extract_actions_from_xml(root)

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


def parse_json_file(file_path, relative_path, extract_variables_from_json, logger):
    try:
        with open(file_path, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)

        description = ""
        if isinstance(data, dict):
            description = data.get("description", data.get("Description", ""))

        variables = extract_variables_from_json(data)
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


def extract_variables_from_xml(root, logger):
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


def extract_variables_from_json(data, logger):
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


def extract_actions_from_xml(root, logger):
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
