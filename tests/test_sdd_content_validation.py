"""Test to validate SDD Word has all Markdown sections."""
from pathlib import Path
from app.generator.sdd_generator import generate_sdd
from app.generator.word_generator import generate_sdd_word
from app.analysis.tree_builder import build_tree


def test_sdd_word_vs_markdown_content():
    """Validate SDD Word document has all sections from Markdown."""
    # Load sample project data
    project_data = {
        "name": "Test Bot",
        "task_count": 2,
        "tasks": [
            {
                "name": "Main",
                "type": "taskbot",
                "description": "Main bot",
                "developer": "Dev",
                "node_stats": {"nodes": 10, "conditions": 2, "loops": 1, "errors": 0, "disabled_nodes": 0},
                "error_handling": {"has_try": True, "has_catch": True, "has_finally": False},
                "actions": [{"name": "action1", "type": "UI"}],
                "packages": [],
                "systems": [],
                "variables": {"input": [], "output": [], "internal": []},
            }
        ],
        "credentials": [],
        "systems": [],
        "packages": [],
        "metadata": {"entrypoints": ["Main"]},
        "files": {"manifest_count": 1},
    }

    # Generate SDD Markdown
    tree_text = "📁 project\n  └── 📁 bots\n      └── 🤖 Main"
    md_content = generate_sdd(project_data, tree_text)
    
    print("\n=== SDD MARKDOWN CONTENT (first 2000 chars) ===")
    print(md_content[:2000])
    
    print("\n=== KEY MARKDOWN SECTIONS ===")
    md_sections = {
        "Tabla de Contenido": "Tabla de Contenido" in md_content,
        "Informacion General": "Informacion General" in md_content,
        "Resumen Ejecutivo": "Resumen Ejecutivo" in md_content,
        "Estadisticas": "Estadisticas" in md_content,
        "Flujo Principal": "Flujo Principal" in md_content,
        "Contrato de Dependencias": "Contrato de Dependencias" in md_content,
        "Inventario de Taskbots": "Inventario de Taskbots" in md_content,
        "Contrato de Variables": "Contrato de Variables" in md_content,
        "Credenciales": "Credenciales" in md_content,
        "Sistemas Externos": "Sistemas Externos" in md_content,
        "Paquetes AA360": "Paquetes AA360" in md_content,
        "Puntos Criticos": "Puntos Criticos" in md_content,
        "Estructura del Proyecto": "Estructura del Proyecto" in md_content,
    }
    
    for section, present in md_sections.items():
        status = "✓" if present else "✗"
        print(f"  {status} {section}: {present}")
    
    # Generate SDD Word
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        word_path = tmp.name
    
    try:
        generate_sdd_word(project_data, tree_text, word_path)
        
        # Read the Word document
        from docx import Document
        doc = Document(word_path)
        word_text = "\n".join(p.text for p in doc.paragraphs)
        
        print("\n=== SDD WORD CONTENT (first 1500 chars) ===")
        print(word_text[:1500])
        
        print("\n=== KEY WORD SECTIONS ===")
        word_sections = {
            "Tabla de Contenido": "Tabla de Contenido" in word_text,
            "Informacion General": "Informacion General" in word_text,
            "Resumen Ejecutivo": "Resumen Ejecutivo" in word_text,
            "Estadisticas": "Estadisticas" in word_text,
            "Flujo Principal": "Flujo Principal" in word_text,
            "Contrato de Dependencias": "Contrato de Dependencias" in word_text,
            "Inventario de Taskbots": "Inventario de Taskbots" in word_text,
            "Contrato de Variables": "Contrato de Variables" in word_text,
            "Credenciales": "Credenciales" in word_text,
            "Sistemas Externos": "Sistemas Externos" in word_text,
            "Paquetes AA360": "Paquetes AA360" in word_text,
            "Puntos Criticos": "Puntos Criticos" in word_text,
            "Estructura del Proyecto": "Estructura del Proyecto" in word_text,
        }
        
        for section, present in word_sections.items():
            status = "✓" if present else "✗"
            print(f"  {status} {section}: {present}")
        
        print("\n=== COMPARISON ===")
        print("Markdown sections present:", sum(md_sections.values()), "/", len(md_sections))
        print("Word sections present:", sum(word_sections.values()), "/", len(word_sections))
        
        # Missing sections
        missing = [s for s in md_sections if md_sections[s] and not word_sections.get(s, False)]
        if missing:
            print("\n=== MISSING IN WORD ===")
            for section in missing:
                print(f"  ✗ {section}")
        else:
            print("\n✓ All sections present in Word")
        
    finally:
        Path(word_path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_sdd_word_vs_markdown_content()
