import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

def generate_sdd(project_data, tree, diagram, flow=None):
    """
    Genera el documento SDD (Software Design Document) en formato Markdown.
    
    Args:
        project_data (dict): Datos del proyecto
        tree (str): Árbol de directorios en formato ASCII
        diagram (str): Diagrama Mermaid del flujo
        flow (dict): Estructura del flujo (opcional)
        
    Returns:
        str: Contenido del SDD en Markdown
    """
    try:
        template_path = Path("app/templates/sdd_template.md")
        
        if not template_path.exists():
            logger.warning(f"Plantilla no encontrada: {template_path}")
            # Usar plantilla por defecto si no existe
            sdd_content = _generate_default_template()
        else:
            with open(template_path, "r", encoding="utf-8") as f:
                sdd_content = f.read()
        
        # Preparar datos para llenar la plantilla
        project_name = project_data.get("name", "Proyecto sin nombre")
        tasks = project_data.get("tasks", [])
        metadata = project_data.get("metadata", {})
        
        # Generar lista de tareas con detalles extendidos
        tasks_details = _generate_tasks_section(tasks)
        
        # Generar tabla de variables por tarea
        variables_table = _generate_variables_table(tasks)
        
        # Generar sección de estadísticas
        stats_section = _generate_stats_section(project_data, flow)
        
        # Generar sección de metadatos
        metadata_section = _generate_metadata_section(metadata)
        
        # Llenar la plantilla
        sdd = sdd_content.format(
            name=project_name,
            description=metadata.get("description", "Documentación auto-generada del bot RPA"),
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tree=tree,
            diagram=diagram,
            tasks=tasks_details,
            variables_table=variables_table,
            statistics=stats_section,
            metadata=metadata_section
        )
        
        logger.info(f"SDD generado exitosamente para: {project_name}")
        return sdd
    
    except Exception as e:
        logger.error(f"Error generando SDD: {str(e)}")
        raise


def generate_sdd_file(project_data, tree, diagram, output_path, flow=None):
    """
    Genera el SDD y lo guarda en un archivo.
    
    Args:
        project_data (dict): Datos del proyecto
        tree (str): Árbol de directorios
        diagram (str): Diagrama Mermaid
        output_path (str): Ruta donde guardar el archivo
        flow (dict): Estructura del flujo (opcional)
        
    Returns:
        str: Ruta del archivo generado
    """
    try:
        sdd_content = generate_sdd(project_data, tree, diagram, flow)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sdd_content)
        
        logger.info(f"Archivo SDD guardado en: {output_file}")
        return str(output_file)
    
    except Exception as e:
        logger.error(f"Error guardando archivo SDD: {str(e)}")
        raise


def _generate_tasks_section(tasks):
    """Genera la sección detallada de tareas con descripción."""
    if not tasks:
        return "No hay tareas en el proyecto."
    
    tasks_list = []
    
    for i, task in enumerate(tasks, 1):
        task_name = task.get("name", f"Tarea {i}")
        task_type = task.get("type", "unknown")
        task_size = task.get("size", 0)
        description = task.get("description", "Sin descripción disponible")
        
        size_str = _format_size(task_size)
        
        # Crear sección para cada tarea
        task_section = f"### {i}. {task_name}\n\n"
        task_section += f"**Tipo:** `{task_type}` | **Tamaño:** {size_str}\n\n"
        task_section += f"**Descripción:** {description}\n\n"
        
        # Agregar información de acciones si existe
        actions = task.get("actions", [])
        if actions:
            task_section += "**Pasos/Acciones:**\n"
            for action in actions:
                action_name = action.get("name", "Paso")
                action_desc = action.get("description", "")
                action_type = action.get("type", "")
                task_section += f"- {action_name} ({action_type})"
                if action_desc:
                    task_section += f": {action_desc}"
                task_section += "\n"
            task_section += "\n"
        
        # Agregar información de atributos si existe
        attributes = task.get("attributes", {})
        if attributes:
            task_section += "**Atributos:**\n"
            for key, value in attributes.items():
                task_section += f"- `{key}`: {value}\n"
            task_section += "\n"
        
        tasks_list.append(task_section)
    
    return "".join(tasks_list)


def _generate_variables_table(tasks):
    """Genera una tabla de variables de entrada y salida por tarea."""
    if not tasks:
        return "No hay variables registradas."
    
    table = "## Variables de Entrada y Salida por Tarea\n\n"
    
    has_variables = False
    
    for i, task in enumerate(tasks, 1):
        task_name = task.get("name", f"Tarea {i}").replace(".xml", "").replace(".json", "")
        variables = task.get("variables", {"input": [], "output": []})
        
        input_vars = variables.get("input", [])
        output_vars = variables.get("output", [])
        
        if input_vars or output_vars:
            has_variables = True
            table += f"### {task_name}\n\n"
            
            # Tabla de entrada
            if input_vars:
                table += "**Variables de Entrada:**\n\n"
                table += "| Nombre | Tipo | Valor |\n"
                table += "|--------|------|-------|\n"
                for var in input_vars:
                    name = var.get("name", "N/A")
                    var_type = var.get("type", "String")
                    value = var.get("value", "")
                    table += f"| {name} | {var_type} | {value} |\n"
                table += "\n"
            
            # Tabla de salida
            if output_vars:
                table += "**Variables de Salida:**\n\n"
                table += "| Nombre | Tipo | Valor |\n"
                table += "|--------|------|-------|\n"
                for var in output_vars:
                    name = var.get("name", "N/A")
                    var_type = var.get("type", "String")
                    value = var.get("value", "")
                    table += f"| {name} | {var_type} | {value} |\n"
                table += "\n"
    
    if not has_variables:
        return "No hay variables de entrada/salida registradas en las tareas."
    
    return table


def _generate_stats_section(project_data, flow=None):
    """Genera la sección de estadísticas."""
    stats = []
    
    tasks = project_data.get("tasks", [])
    file_counts = project_data.get("files", {})
    
    stats.append(f"- **Total de tareas:** {len(tasks)}")
    stats.append(f"- **Archivos XML:** {file_counts.get('xml_count', 0)}")
    stats.append(f"- **Archivos JSON:** {file_counts.get('json_count', 0)}")
    
    if flow and "summary" in flow:
        summary = flow["summary"]
        stats.append(f"- **Nodos en flujo:** {summary.get('total_nodes', 0)}")
        stats.append(f"- **Conexiones:** {summary.get('total_edges', 0)}")
    
    # Calcular tamaño total
    total_size = sum(t.get("size", 0) for t in tasks)
    stats.append(f"- **Tamaño total:** {_format_size(total_size)}")
    
    return "\n".join(stats)


def _generate_metadata_section(metadata):
    """Genera la sección de metadatos."""
    if not metadata:
        return "No hay metadatos disponibles."
    
    metadata_list = []
    for key, value in metadata.items():
        # Esconder datos sensibles
        if key.lower() in ['password', 'token', 'secret', 'api_key']:
            value = "***"
        
        metadata_list.append(f"- **{key}:** {value}")
    
    return "\n".join(metadata_list)


def _format_size(bytes_size):
    """Convierte bytes a formato legible."""
    if bytes_size is None:
        return "0B"
    
    bytes_size = int(bytes_size)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f}TB"


def _generate_default_template():
    """Retorna una plantilla por defecto si no existe."""
    return """# SDD - {name}

## 1. Información General
- **Nombre del Bot:** {name}
- **Descripción:** {description}
- **Fecha de Generación:** {generated_date}

## 2. Estadísticas
{statistics}

## 3. Estructura del Proyecto
```
{tree}
```

## 4. Flujo de Procesos
{diagram}

## 5. Detalle de Tareas
{tasks}

## 6. Variables de Entrada y Salida
{variables_table}

## 7. Metadatos
{metadata}

---
*Documento generado automáticamente por RPA-Doc-Generator*
"""

