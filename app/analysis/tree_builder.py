import os
import logging

logger = logging.getLogger(__name__)

# Carpetas y archivos a excluir
EXCLUDED_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}
EXCLUDED_EXTENSIONS = {'.jar', '.class', '.pyc', '.pyo', '__pycache__'}

def build_tree(path, prefix="", include_stats=True):
    """
    Construye una representación visual del árbol de directorios con estadísticas.
    Excluye carpetas de metadata y archivos .jar
    
    Args:
        path (str): Ruta del directorio
        prefix (str): Prefijo para la indentación (interno)
        include_stats (bool): Incluir estadísticas de archivos
        
    Returns:
        str: Representación ASCII del árbol
    """
    try:
        tree = ""
        files = sorted(os.listdir(path))
        
        # Filtrar items excluidos
        files = [f for f in files if not should_exclude(f)]
        
        # Separar directorios y archivos
        dirs = [f for f in files if os.path.isdir(os.path.join(path, f))]
        file_list = [f for f in files if os.path.isfile(os.path.join(path, f))]
        
        all_items = dirs + file_list
        
        for i, file in enumerate(all_items):
            full_path = os.path.join(path, file)
            is_last = i == len(all_items) - 1
            connector = "└── " if is_last else "├── "
            
            # Agregar icono según tipo
            if os.path.isdir(full_path):
                icon = "📁 "
                display_name = file + "/"
            else:
                ext = os.path.splitext(file)[1]
                if ext == ".xml":
                    icon = "📄 "
                elif ext == ".json":
                    icon = "📋 "
                else:
                    icon = "📃 "
                display_name = file
                
                # Agregar tamaño del archivo
                if include_stats:
                    size = os.path.getsize(full_path)
                    size_str = _format_size(size)
                    display_name += f" ({size_str})"
            
            tree += prefix + connector + icon + display_name + "\n"
            
            # Recursivamente agregar subdirectorios
            if os.path.isdir(full_path):
                extension = "    " if is_last else "│   "
                tree += build_tree(full_path, prefix + extension, include_stats)
        
        return tree
    
    except Exception as e:
        logger.error(f"Error construyendo árbol: {str(e)}")
        return f"Error: {str(e)}"


def should_exclude(filename):
    """Determina si un archivo/carpeta debe ser excluido."""
    # Excluir carpetas que contengan "metadata" en su nombre (cualquier caso)
    if "metadata" in filename.lower():
        return True
    
    # Excluir extensiones
    ext = os.path.splitext(filename)[1].lower()
    if ext in EXCLUDED_EXTENSIONS:
        return True
    
    # Excluir archivos ocultos en Unix
    if filename.startswith('.'):
        return True
    
    return False


def _format_size(bytes_size):
    """Convierte bytes a formato legible."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f}TB"
