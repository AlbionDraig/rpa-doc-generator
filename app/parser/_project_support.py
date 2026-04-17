from collections import Counter
from pathlib import Path

from app.parser._common import (
    TASKBOT_CONTENT_TYPE,
    TASKBOT_HINT_KEYS,
    _load_json,
    _looks_like_taskbot,
    _normalize_path_text,
    _sanitize_mapping,
    _sanitize_packages,
    _sanitize_triggers,
    _should_skip_file,
)


def discover_task_entries(project_root, manifest):
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


def parse_taskbot(task_path, project_root, data, manifest_entry, extract_header_metadata, analyze_nodes, extract_taskbot_variables, merge_dependencies, detect_role):
    relative_path = str(task_path.relative_to(project_root))
    header = extract_header_metadata(data.get("nodes", []))
    node_analysis = analyze_nodes(data.get("nodes", []))
    variables = extract_taskbot_variables(data.get("variables", []))
    dependencies = merge_dependencies(manifest_entry, node_analysis["task_calls"])
    role = detect_role(relative_path, task_path.name)

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
        "credentials": node_analysis["credentials"],
        "comments": node_analysis["comments"],
    }


def merge_dependencies(manifest_entry, task_calls):
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


def detect_role(relative_path, task_name):
    normalized_path = relative_path.replace("/", "\\").lower()
    if task_name.lower() == "main":
        return "main"
    if "\\tareas\\" in normalized_path or "\\subtasks\\" in normalized_path:
        return "subtask"
    return "taskbot"


def mark_entrypoints(tasks):
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


def build_manifest_summary(manifest):
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


def collect_project_packages(manifest_summary, tasks):
    packages_by_name = {}

    for package in manifest_summary.get("packages", []):
        packages_by_name[package["name"]] = package

    for task in tasks:
        for package in task.get("packages", []):
            packages_by_name[package["name"]] = package

    return sorted(packages_by_name.values(), key=lambda item: item["name"].lower())


def collect_project_systems(tasks):
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


def collect_project_credentials(tasks):
    credentials = []
    seen = set()

    for task in tasks:
        for credential in task.get("credentials", []):
            signature = (credential["credential_name"], credential.get("attribute", ""))
            if signature in seen:
                continue
            seen.add(signature)
            credentials.append(credential)

    return sorted(credentials, key=lambda item: (item.get("vault", ""), item["credential_name"]))


def select_project_description(tasks):
    for task in tasks:
        description = task.get("description")
        if description:
            return description
    return "Documentacion auto-generada del bot RPA"


def build_file_summary(project_root, manifest, tasks):
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
