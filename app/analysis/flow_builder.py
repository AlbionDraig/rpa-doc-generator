import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


def build_flow(tasks):
    """
    Construye el flujo entre taskbots usando dependencias reales.

    Cada arista representa una invocacion `runTask` o una dependencia
    detectada en el `manifest.json`.
    """
    if not tasks:
        logger.warning("No hay tareas para construir el flujo")
        return {
            "nodes": [],
            "edges": [],
            "summary": {
                "total_nodes": 0,
                "total_edges": 0,
                "entrypoints": [],
            },
        }

    nodes = []
    path_to_id = {}

    for index, task in enumerate(tasks, start=1):
        node_id = f"task_{index}"
        path_to_id[task["path"]] = node_id
        nodes.append(
            {
                "id": node_id,
                "name": task.get("name", f"Tarea {index}"),
                "path": task.get("path", ""),
                "role": task.get("role", "taskbot"),
                "is_entrypoint": bool(task.get("is_entrypoint")),
                "type": task.get("type", "taskbot"),
                "order": index,
                "node_count": task.get("node_stats", {}).get("total_nodes", 0),
            }
        )

    edges = []
    seen_edges = set()

    for task in tasks:
        source_id = path_to_id[task["path"]]
        task_calls_by_target = {
            task_call.get("target_path"): task_call
            for task_call in task.get("task_calls", [])
            if task_call.get("target_path")
        }
        for dependency in task.get("dependencies", []):
            dependency_path = dependency.get("path")
            target_id = path_to_id.get(dependency_path)
            if not target_id:
                continue

            edge_key = (source_id, target_id)
            if edge_key in seen_edges:
                continue

            seen_edges.add(edge_key)
            task_call = task_calls_by_target.get(dependency_path)
            edges.append(
                {
                    "from": source_id,
                    "to": target_id,
                    "label": dependency.get("type", "dependency"),
                    "inputs_count": len(task_call.get("inputs", [])) if task_call else 0,
                    "outputs_count": len(task_call.get("outputs", [])) if task_call else 0,
                }
            )

    ordered_nodes = _sort_nodes(nodes, edges)
    order_lookup = {node["id"]: position for position, node in enumerate(ordered_nodes, start=1)}
    for node in ordered_nodes:
        node["order"] = order_lookup[node["id"]]

    entrypoints = [node["name"] for node in ordered_nodes if node.get("is_entrypoint")]
    summary = {
        "total_nodes": len(ordered_nodes),
        "total_edges": len(edges),
        "entrypoints": entrypoints,
        "has_dependencies": bool(edges),
    }

    logger.info(
        "Flujo construido: %s nodos, %s aristas, entrypoints=%s",
        len(ordered_nodes),
        len(edges),
        ", ".join(entrypoints) if entrypoints else "sin entrypoints",
    )

    return {
        "nodes": ordered_nodes,
        "edges": edges,
        "summary": summary,
    }


def _sort_nodes(nodes, edges):
    adjacency = defaultdict(list)
    incoming_count = {node["id"]: 0 for node in nodes}
    node_by_id = {node["id"]: node for node in nodes}

    for edge in edges:
        adjacency[edge["from"]].append(edge["to"])
        incoming_count[edge["to"]] += 1

    queue = deque(
        sorted(
            (node for node in nodes if incoming_count[node["id"]] == 0),
            key=lambda item: (0 if item.get("is_entrypoint") else 1, item["order"], item["name"].lower()),
        )
    )
    ordered = []

    while queue:
        node = queue.popleft()
        ordered.append(node)

        for target_id in sorted(adjacency[node["id"]], key=lambda item: node_by_id[item]["name"].lower()):
            incoming_count[target_id] -= 1
            if incoming_count[target_id] == 0:
                queue.append(node_by_id[target_id])

    if len(ordered) != len(nodes):
        logger.warning("Se detectaron ciclos o dependencias incompletas; se usara el orden original")
        return sorted(nodes, key=lambda item: item["order"])

    return ordered
