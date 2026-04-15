import logging

logger = logging.getLogger(__name__)

def generate_mermaid(flow):
    """
    Genera un diagrama Mermaid del flujo de tareas.
    
    Args:
        flow (dict): Estructura del flujo con nodos y aristas
        
    Returns:
        str: Código Mermaid del diagrama
    """
    try:
        if not flow.get("nodes"):
            logger.warning("No hay nodos para generar diagrama")
            return "graph TD\n    Inicio[No hay tareas]"
        
        diagram = "```mermaid\ngraph TD\n"
        
        # Generar nodos con información adicional
        for node in flow["nodes"]:
            node_id = node["id"]
            node_name = node["name"]
            node_type = node.get("type", "unknown")
            
            # Formatear el nombre del nodo - caracteres válidos para Mermaid
            clean_name = node_name.replace('"', "'").replace('\n', ' ').replace('\r', '')
            
            # Usar formato más simple pero efectivo
            diagram += f"    {node_id}[\"{clean_name}\"]\n"
        
        # Generar aristas (conexiones)
        for edge in flow["edges"]:
            from_id = edge["from"]
            to_id = edge["to"]
            label = edge.get("label", "")
            
            if label:
                diagram += f"    {from_id} -->|{label}| {to_id}\n"
            else:
                diagram += f"    {from_id} --> {to_id}\n"
        
        diagram += "```"
        
        logger.info("Diagrama Mermaid generado exitosamente")
        return diagram
    
    except Exception as e:
        logger.error(f"Error generando diagrama: {str(e)}")
        return f"```mermaid\ngraph TD\n    Error[\"Error: {str(e)}\"]\n```"
