import os
import json
import xml.etree.ElementTree as ET
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def parse_project(path):
    """
    Analiza el proyecto de Automation Anywhere extrayendo información
    de archivos XML y JSON.
    
    Args:
        path (str): Ruta de la carpeta del proyecto extraído
        
    Returns:
        dict: Información del proyecto con tareas y metadatos
    """
    if not os.path.exists(path):
        logger.error(f"Ruta no encontrada: {path}")
        raise FileNotFoundError(f"La ruta {path} no existe")
    
    tasks = []
    metadata = {}
    project_name = os.path.basename(path)
    
    try:
        for root, dirs, files in os.walk(path):
            # Excluir carpetas que contengan "metadata" en el nombre
            dirs[:] = [d for d in dirs if "metadata" not in d.lower()]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, path)
                
                # Excluir archivos .jar
                if file.endswith('.jar'):
                    continue
                
                try:
                    if file.endswith(".xml"):
                        task_info = _parse_xml_file(file_path, relative_path)
                    elif file.endswith(".json"):
                        task_info = _parse_json_file(file_path, relative_path)
                    else:
                        continue
                    
                    if task_info:
                        tasks.append(task_info)
                
                except Exception as e:
                    logger.warning(f"Error parseando {file_path}: {str(e)}")
                    continue
        
        # Extraer metadatos si existe un archivo de configuración
        metadata = _extract_metadata(path)
        
        result = {
            "name": project_name,
            "path": path,
            "tasks": tasks,
            "task_count": len(tasks),
            "metadata": metadata,
            "files": {
                "xml_count": len([t for t in tasks if t.get("type") == "xml"]),
                "json_count": len([t for t in tasks if t.get("type") == "json"])
            }
        }
        
        logger.info(f"Proyecto parseado: {project_name} con {len(tasks)} tareas")
        return result
    
    except Exception as e:
        logger.error(f"Error parseando proyecto: {str(e)}")
        raise


def _parse_xml_file(file_path, relative_path):
    """Extrae información de un archivo XML incluyendo detalles de tareas."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Obtener información del nodo raíz
        tag = root.tag
        attributes = root.attrib
        
        # Contar elementos hijo
        children_count = len(root)
        
        # Extraer descripción si existe
        description = attributes.get('Description', attributes.get('description', ''))
        
        # Extraer variables de entrada/salida
        variables = _extract_variables_from_xml(root)
        
        # Extraer acciones/pasos
        actions = _extract_actions_from_xml(root)
        
        return {
            "name": os.path.basename(file_path),
            "path": relative_path,
            "type": "xml",
            "tag": tag,
            "description": description,
            "attributes": attributes,
            "elements_count": children_count,
            "size": os.path.getsize(file_path),
            "variables": variables,
            "actions": actions
        }
    except Exception as e:
        logger.debug(f"Error parseando XML {file_path}: {str(e)}")
        return None


def _parse_json_file(file_path, relative_path):
    """Extrae información de un archivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extraer descripción
        description = ''
        if isinstance(data, dict):
            description = data.get('description', data.get('Description', ''))
        
        # Extraer variables
        variables = _extract_variables_from_json(data)
        
        return {
            "name": os.path.basename(file_path),
            "path": relative_path,
            "type": "json",
            "description": description,
            "keys": list(data.keys()) if isinstance(data, dict) else None,
            "items_count": len(data) if isinstance(data, (dict, list)) else 0,
            "size": os.path.getsize(file_path),
            "variables": variables
        }
    except Exception as e:
        logger.debug(f"Error parseando JSON {file_path}: {str(e)}")
        return None


def _extract_variables_from_xml(root):
    """Extrae variables de entrada/salida de un elemento XML."""
    variables = {
        "input": [],
        "output": []
    }
    
    try:
        # Buscar elementos de variable
        for elem in root.iter():
            # Variables de entrada
            if 'input' in elem.tag.lower() or 'parameter' in elem.tag.lower():
                var_info = {
                    "name": elem.attrib.get('Name', elem.attrib.get('name', 'Unknown')),
                    "type": elem.attrib.get('Type', elem.attrib.get('type', 'String')),
                    "value": elem.attrib.get('Value', elem.attrib.get('value', ''))
                }
                if var_info["name"] != "Unknown":
                    variables["input"].append(var_info)
            
            # Variables de salida
            if 'output' in elem.tag.lower() or 'return' in elem.tag.lower():
                var_info = {
                    "name": elem.attrib.get('Name', elem.attrib.get('name', 'Unknown')),
                    "type": elem.attrib.get('Type', elem.attrib.get('type', 'String')),
                    "value": elem.attrib.get('Value', elem.attrib.get('value', ''))
                }
                if var_info["name"] != "Unknown":
                    variables["output"].append(var_info)
    
    except Exception as e:
        logger.debug(f"Error extrayendo variables XML: {str(e)}")
    
    return variables


def _extract_variables_from_json(data):
    """Extrae variables de entrada/salida de un JSON."""
    variables = {
        "input": [],
        "output": []
    }
    
    try:
        if isinstance(data, dict):
            # Buscar secciones de entrada/salida
            for key, value in data.items():
                if 'input' in key.lower():
                    if isinstance(value, dict):
                        for var_name, var_type in value.items():
                            variables["input"].append({
                                "name": var_name,
                                "type": str(type(var_type).__name__)
                            })
                elif 'output' in key.lower():
                    if isinstance(value, dict):
                        for var_name, var_type in value.items():
                            variables["output"].append({
                                "name": var_name,
                                "type": str(type(var_type).__name__)
                            })
    
    except Exception as e:
        logger.debug(f"Error extrayendo variables JSON: {str(e)}")
    
    return variables


def _extract_actions_from_xml(root):
    """Extrae las acciones/pasos de un elemento XML."""
    actions = []
    
    try:
        # Buscar elementos de acción
        for elem in root.iter():
            if 'action' in elem.tag.lower() or 'task' in elem.tag.lower() or 'step' in elem.tag.lower():
                action = {
                    "name": elem.attrib.get('Name', elem.attrib.get('name', 'Paso')),
                    "type": elem.tag,
                    "description": elem.attrib.get('Description', elem.attrib.get('description', ''))
                }
                actions.append(action)
    
    except Exception as e:
        logger.debug(f"Error extrayendo acciones: {str(e)}")
    
    return actions


def _extract_metadata(path):
    """Extrae metadatos del proyecto."""
    metadata = {}
    
    # Buscar archivos de configuración comunes
    for config_file in ['config.json', 'package.json', 'manifest.json', 'project.json']:
        config_path = os.path.join(path, config_file)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    metadata.update(json.load(f))
            except:
                pass
    
    return metadata
