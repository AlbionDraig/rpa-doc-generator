import logging

logger = logging.getLogger(__name__)

def build_flow(tasks):
    """
    Construye un flujo de tareas basado en el orden de los archivos.
    
    Args:
        tasks (list): Lista de tareas del proyecto
        
    Returns:
        dict: Estructura del flujo con nodos y aristas
    """
    if not tasks:
        logger.warning("No hay tareas para construir el flujo")
        return {"nodes": [], "edges": [], "summary": {"total_nodes": 0, "total_edges": 0}}
    
    nodes = []
    edges = []
    
    for i, task in enumerate(tasks):
        node_id = f"task_{i}"
        node_name = task.get("name", f"Tarea {i+1}").replace(".xml", "").replace(".json", "")
        
        node = {
            "id": node_id,
            "name": node_name,
            "type": task.get("type", "unknown"),
            "order": i + 1,
            "size": task.get("size", 0)
        }
        nodes.append(node)
        
        # Crear conexión con la tarea anterior
        if i > 0:
            edges.append({
                "from": f"task_{i-1}",
                "to": node_id,
                "label": "secuencial"
            })
    
    summary = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "start_node": nodes[0]["id"] if nodes else None,
        "end_node": nodes[-1]["id"] if nodes else None
    }
    
    logger.info(f"Flujo construido: {len(nodes)} nodos, {len(edges)} aristas")
    
    return {
        "nodes": nodes,
        "edges": edges,
        "summary": summary
    }
