import logging
import os
from pathlib import Path

from app.parser import _documents, _node_analysis, _project_support
from app.parser._common import (
    HEADER_COMMENT_PREFIXES,
    METADATA_DIR_FRAGMENT,
    SENSITIVE_FIELD_PATTERN,
    TASKBOT_CONTENT_TYPE,
    TASKBOT_HINT_KEYS,
    UI_NOISE_KEYS,
    URL_CREDENTIAL_PATTERN,
    WINDOWS_PATH_PATTERN,
    WINDOWS_USER_PATH_PATTERN,
    _extract_comment_text as _extract_comment_text_impl,
    _extract_value_literal as _extract_value_literal_impl,
    _flatten_attribute_values as _flatten_attribute_values_impl,
    _get_attribute as _get_attribute_impl,
    _get_attribute_string as _get_attribute_string_impl,
    _is_header_comment as _is_header_comment_impl,
    _load_json as _load_json_impl,
    _load_manifest as _load_manifest_impl,
    _looks_like_taskbot as _looks_like_taskbot_impl,
    _normalize_path_text as _normalize_path_text_impl,
    _normalize_repository_path as _normalize_repository_path_impl,
    _sanitize_mapping as _sanitize_mapping_impl,
    _sanitize_packages as _sanitize_packages_impl,
    _sanitize_triggers as _sanitize_triggers_impl,
    _should_skip_file as _should_skip_file_impl,
    sanitize_text as sanitize_text_impl,
)

logger = logging.getLogger(__name__)


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
    project_credentials = _collect_project_credentials(tasks)

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
        "credentials": project_credentials,
    }

    logger.info(
        "Proyecto AA360 parseado: %s con %s taskbots",
        result["name"],
        result["task_count"],
    )
    return result


def _load_manifest(project_root):
    return _load_manifest_impl(project_root, logger)


def _discover_task_entries(project_root, manifest):
    return _project_support.discover_task_entries(project_root, manifest)


def _should_skip_file(file_path):
    return _should_skip_file_impl(file_path)


def _looks_like_taskbot(file_path):
    return _looks_like_taskbot_impl(file_path)


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
    return _project_support.parse_taskbot(
        task_path,
        project_root,
        data,
        manifest_entry,
        extract_header_metadata=_extract_header_metadata,
        analyze_nodes=_analyze_nodes,
        extract_taskbot_variables=_extract_taskbot_variables,
        merge_dependencies=_merge_dependencies,
        detect_role=_detect_role,
    )


def _extract_header_metadata(nodes):
    return _node_analysis.extract_header_metadata(nodes)


def _extract_taskbot_variables(variables):
    return _node_analysis.extract_taskbot_variables(variables, infer_variable_scope=_infer_variable_scope)


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
    return _node_analysis.analyze_nodes(
        nodes,
        extract_task_call=_extract_task_call,
        summarize_node=_summarize_node,
        should_keep_summary=_should_keep_summary,
    )


def _visit_node(node, analysis, seen_systems, depth):
    return _node_analysis.visit_node(
        node,
        analysis,
        seen_systems,
        depth,
        extract_task_call=_extract_task_call,
        summarize_node=_summarize_node,
        should_keep_summary=_should_keep_summary,
    )


def _should_keep_summary(node, depth):
    return _node_analysis.should_keep_summary(node, depth)


def _summarize_node(node, depth):
    return _node_analysis.summarize_node(node, depth, extract_task_call=_extract_task_call)


def _extract_task_call(node):
    return _node_analysis.extract_task_call(node)


def _merge_dependencies(manifest_entry, task_calls):
    return _project_support.merge_dependencies(manifest_entry, task_calls)


def _detect_role(relative_path, task_name):
    return _project_support.detect_role(relative_path, task_name)


def _mark_entrypoints(tasks):
    return _project_support.mark_entrypoints(tasks)


def _build_manifest_summary(manifest):
    return _project_support.build_manifest_summary(manifest)


def _collect_project_packages(manifest_summary, tasks):
    return _project_support.collect_project_packages(manifest_summary, tasks)


def _collect_project_systems(tasks):
    return _project_support.collect_project_systems(tasks)


def _collect_project_credentials(tasks):
    return _project_support.collect_project_credentials(tasks)


def _select_project_description(tasks):
    return _project_support.select_project_description(tasks)


def _build_file_summary(project_root, manifest, tasks):
    return _project_support.build_file_summary(project_root, manifest, tasks)


def _sanitize_packages(packages):
    return _sanitize_packages_impl(packages)


def _sanitize_triggers(triggers):
    return _sanitize_triggers_impl(triggers)


def _sanitize_mapping(mapping):
    return _sanitize_mapping_impl(mapping)


def sanitize_text(value, field_name=None):
    return sanitize_text_impl(value, field_name=field_name)


def _extract_credential_from_node(node):
    return _node_analysis.extract_credential_from_node(node)


def _extract_systems_from_node(node):
    return _node_analysis.extract_systems_from_node(node)


def _flatten_attribute_values(value, parent_key=None):
    return _flatten_attribute_values_impl(value, parent_key=parent_key)


def _extract_comment_text(node):
    return _extract_comment_text_impl(node)


def _is_header_comment(comment_text):
    return _is_header_comment_impl(comment_text)


def _get_attribute(node, name):
    return _get_attribute_impl(node, name)


def _get_attribute_string(node, name):
    return _get_attribute_string_impl(node, name)


def _extract_value_literal(value):
    return _extract_value_literal_impl(value)


def _normalize_repository_path(repository_path):
    return _normalize_repository_path_impl(repository_path)


def _normalize_path_text(path_text):
    return _normalize_path_text_impl(path_text)


def _load_json(file_path):
    return _load_json_impl(file_path)


def _parse_xml_file(file_path, relative_path):
    return _documents.parse_xml_file(
        file_path,
        relative_path,
        extract_variables_from_xml=_extract_variables_from_xml,
        extract_actions_from_xml=_extract_actions_from_xml,
        logger=logger,
    )


def _parse_json_file(file_path, relative_path):
    return _documents.parse_json_file(
        file_path,
        relative_path,
        extract_variables_from_json=_extract_variables_from_json,
        logger=logger,
    )


def _extract_variables_from_xml(root):
    return _documents.extract_variables_from_xml(root, logger)


def _extract_variables_from_json(data):
    return _documents.extract_variables_from_json(data, logger)


def _extract_actions_from_xml(root):
    return _documents.extract_actions_from_xml(root, logger)
