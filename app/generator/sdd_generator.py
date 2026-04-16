import logging
from datetime import datetime
from pathlib import Path

from app.analysis.task_ai_describer import (
    build_sdd_ai_insights,
    build_quality_prioritization,
    build_quality_task_descriptions,
    classify_task_for_aa360,
)

logger = logging.getLogger(__name__)

def generate_sdd(project_data, tree, flow=None, flow_visual=None):
    """
    Genera el documento SDD en Markdown a partir del modelo AA360 ya parseado.
    """
    try:
        template = _load_template()
        tasks = project_data.get("tasks", [])
        metadata = project_data.get("metadata", {})
        sdd_ai_insights = build_sdd_ai_insights(project_data, flow)

        rendered = template.format(
            name=project_data.get("name", "Proyecto sin nombre"),
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            toc=_generate_toc(project_data),
            executive_summary=_generate_executive_summary_section(sdd_ai_insights),
            overview=_generate_overview(project_data, flow),
            statistics=_generate_stats_section(project_data, flow),
            flow_visual=flow_visual or _generate_flow_visual_placeholder(),
            dependency_contracts=_generate_dependency_contracts(tasks),
            task_inventory=_generate_task_inventory(tasks),
            variables_section=_generate_variables_section(tasks),
            credentials_section=_generate_credentials_section(project_data),
            systems_section=_generate_systems_section(project_data),
            packages_section=_generate_packages_section(project_data),
            critical_points=_generate_critical_points_section(sdd_ai_insights),
            tree=tree,
        )

        logger.info("SDD generado exitosamente para: %s", project_data.get("name"))
        return rendered
    except Exception as exc:
        logger.error("Error generando SDD: %s", exc)
        raise


def generate_sdd_file(project_data, tree, output_path, flow=None, flow_visual=None):
    """
    Genera el SDD y lo guarda en un archivo.
    """
    try:
        sdd_content = generate_sdd(project_data, tree, flow, flow_visual)
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as file_obj:
            file_obj.write(sdd_content)

        logger.info("Archivo SDD guardado en: %s", output_file)
        return str(output_file)
    except Exception as exc:
        logger.error("Error guardando archivo SDD: %s", exc)
        raise


def _load_template():
    template_path = Path("app/templates/sdd_template.md")
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return _generate_default_template()


def _generate_overview(project_data, flow):
    files = project_data.get("files", {})
    metadata = project_data.get("metadata", {})
    entrypoints = metadata.get("entrypoints", [])
    packages = project_data.get("packages", [])
    systems = project_data.get("systems", [])

    lines = [
        f"- **Nombre del bot:** {project_data.get('name', 'N/A')}",
        f"- **Descripcion funcional:** {metadata.get('description', 'No disponible')}",
        f"- **Taskbots detectados:** {project_data.get('task_count', 0)}",
        f"- **Entrypoints:** {', '.join(entrypoints) if entrypoints else 'No identificados'}",
        f"- **Paquetes AA360 usados:** {len(packages)}",
        f"- **Sistemas externos detectados:** {len(systems)}",
        f"- **Manifest presente:** {'Si' if files.get('manifest_count') else 'No'}",
    ]

    if flow:
        lines.append(f"- **Dependencias entre taskbots:** {flow.get('summary', {}).get('total_edges', 0)}")

    return "\n".join(lines)


def _generate_executive_summary_section(sdd_ai_insights):
    summary = sdd_ai_insights.get("executive_summary", [])
    source = sdd_ai_insights.get("source", "heuristic")
    confidence = sdd_ai_insights.get("confidence", "media")

    if not summary:
        return "No se pudo generar resumen ejecutivo."

    lines = [
        f"- **Fuente de analisis:** {source}",
        f"- **Confianza estimada:** {confidence}",
        "",
    ]
    lines.extend(f"- {item}" for item in summary)
    return "\n".join(lines)


def _generate_stats_section(project_data, flow):
    tasks = project_data.get("tasks", [])
    files = project_data.get("files", {})

    total_nodes = sum(task.get("node_stats", {}).get("total_nodes", 0) for task in tasks)
    decision_nodes = sum(task.get("node_stats", {}).get("decision_nodes", 0) for task in tasks)
    loop_nodes = sum(task.get("node_stats", {}).get("loop_nodes", 0) for task in tasks)
    task_calls = sum(task.get("node_stats", {}).get("task_calls", 0) for task in tasks)
    error_handlers = sum(task.get("node_stats", {}).get("error_handlers", 0) for task in tasks)
    total_size = sum(task.get("size", 0) for task in tasks)

    lines = [
        f"- **Total de taskbots:** {len(tasks)}",
        f"- **Archivos XML auxiliares:** {files.get('xml_count', 0)}",
        f"- **Archivos JSON auxiliares:** {files.get('json_count', 0)}",
        f"- **Nodos AA360 analizados:** {total_nodes}",
        f"- **Condiciones detectadas:** {decision_nodes}",
        f"- **Bucles o reintentos:** {loop_nodes}",
        f"- **Invocaciones `runTask`:** {task_calls}",
        f"- **Bloques de manejo de errores:** {error_handlers}",
        f"- **Tamano total taskbots:** {_format_size(total_size)}",
    ]

    if flow:
        lines.append(f"- **Aristas de flujo entre taskbots:** {flow.get('summary', {}).get('total_edges', 0)}")

    return "\n".join(lines)


def _generate_task_inventory(tasks):
    if not tasks:
        return "No se detectaron taskbots en el paquete exportado."

    sections = []
    for index, task in enumerate(tasks, start=1):
        sections.append(f"### {index}. {task.get('name', 'Taskbot')}")
        sections.append("")
        sections.append(f"- **Rol:** {task.get('role', 'taskbot')}")
        sections.append(f"- **Perfil AA360 sugerido:** {classify_task_for_aa360(task)}")
        sections.append(f"- **Ruta:** `{task.get('path', '')}`")
        sections.append(f"- **Entrypoint:** {'Si' if task.get('is_entrypoint') else 'No'}")
        sections.append(f"- **Tamano:** {_format_size(task.get('size', 0))}")
        if task.get("description"):
            sections.append(f"- **Descripcion declarada:** {task['description']}")
        if task.get("developer"):
            sections.append(f"- **Developer declarado:** {task['developer']}")
        if task.get("declared_date"):
            sections.append(f"- **Fecha declarada:** {task['declared_date']}")

        sections.append(
            "- **Resumen estructural:** "
            f"{task.get('node_stats', {}).get('total_nodes', 0)} nodos, "
            f"{task.get('node_stats', {}).get('decision_nodes', 0)} condiciones, "
            f"{task.get('node_stats', {}).get('loop_nodes', 0)} bucles, "
            f"{task.get('node_stats', {}).get('task_calls', 0)} llamadas a subtasks"
        )
        sections.append(f"- **Manejo de errores:** {_describe_error_handling(task.get('error_handling', {}))}")

        dependencies = task.get("dependencies", [])
        dependency_label = ", ".join(
            f"{dependency['name']} ({dependency['type']})" for dependency in dependencies
        )
        sections.append(f"- **Dependencias:** {dependency_label if dependency_label else 'Sin dependencias'}")

        task_calls = task.get("task_calls", [])
        if task_calls:
            call_summaries = [
                f"{call['target_name']} [{len(call.get('inputs', []))} in / {len(call.get('outputs', []))} out]"
                for call in task_calls
            ]
            sections.append(f"- **Subtasks invocadas:** {', '.join(call_summaries)}")

        packages = task.get("packages", [])
        if packages:
            package_summary = ", ".join(
                f"{package['name']} {package['version']}".strip() for package in packages[:10]
            )
            sections.append(f"- **Paquetes usados por el taskbot:** {package_summary}")

        actions = _unique_preserve(task.get("actions", []))[:10]
        if actions:
            sections.append("- **Pasos principales:**")
            sections.extend(f"  - {action}" for action in actions)

        comments = _unique_preserve(task.get("comments", []))[:5]
        if comments:
            sections.append("- **Comentarios funcionales relevantes:**")
            sections.extend(f"  - {comment}" for comment in comments)

        systems = task.get("systems", [])
        if systems:
            system_summary = ", ".join(
                f"{system['type']}: {system['value']}" for system in systems[:5]
            )
            sections.append(f"- **Sistemas y endpoints detectados:** {system_summary}")

        sections.append("")

    return "\n".join(sections).rstrip()


def _generate_variables_section(tasks):
    if not tasks:
        return "No se detectaron variables documentables."

    sections = []
    for task in tasks:
        variables = task.get("variables", {})
        input_vars = variables.get("input", [])
        output_vars = variables.get("output", [])
        internal_vars = variables.get("internal", [])

        sections.append(f"### {task.get('name', 'Taskbot')}")
        sections.append("")
        sections.append(
            f"- **Resumen:** {len(input_vars)} inputs, {len(output_vars)} outputs, {len(internal_vars)} internas"
        )

        if input_vars:
            sections.append("")
            sections.append("**Variables de entrada**")
            sections.append("")
            sections.append("| Nombre | Tipo | Default | Descripcion |")
            sections.append("|--------|------|---------|-------------|")
            for variable in input_vars:
                sections.append(
                    f"| {variable['name']} | {variable['type']} | {variable['default'] or '-'} | {variable['description'] or '-'} |"
                )

        if output_vars:
            sections.append("")
            sections.append("**Variables de salida**")
            sections.append("")
            sections.append("| Nombre | Tipo | Default | Descripcion |")
            sections.append("|--------|------|---------|-------------|")
            for variable in output_vars:
                sections.append(
                    f"| {variable['name']} | {variable['type']} | {variable['default'] or '-'} | {variable['description'] or '-'} |"
                )

        if internal_vars:
            sections.append("")
            sections.append("**Variables internas relevantes**")
            sections.append("")
            sections.append("| Nombre | Tipo | Scope | Default |")
            sections.append("|--------|------|-------|---------|")
            for variable in internal_vars[:12]:
                sections.append(
                    f"| {variable['name']} | {variable['type']} | {variable['scope']} | {variable['default'] or '-'} |"
                )

        sections.append("")

    return "\n".join(sections).rstrip()


def _generate_credentials_section(project_data):
    credentials = project_data.get("credentials", [])
    if not credentials:
        return "No se detectaron credenciales o vaults en los taskbots."

    lines = ["| Credencial | Atributo | Vault | Origen |", "|------------|----------|-------|--------|"]  
    for credential in credentials:
        lines.append(
            f"| {credential['credential_name']} "
            f"| {credential.get('attribute', '-') or '-'} "
            f"| {credential.get('vault', '-') or '-'} "
            f"| `{credential.get('source', '-')}` |"
        )
    return "\n".join(lines)


def _generate_systems_section(project_data):
    systems = project_data.get("systems", [])
    if not systems:
        return "No se detectaron sistemas externos o configuraciones tecnicas relevantes."

    lines = []
    for system in systems:
        lines.append(
            f"- **{system['type']}**: `{system['value']}` (origen: `{system['source']}`)"
        )
    return "\n".join(lines)


def _generate_packages_section(project_data):
    packages = project_data.get("packages", [])
    if not packages:
        return "No se detectaron paquetes de AA360."

    lines = ["| Paquete | Version |", "|---------|---------|"]
    for package in packages:
        lines.append(f"| {package['name']} | {package['version'] or '-'} |")
    return "\n".join(lines)


def _generate_critical_points_section(sdd_ai_insights):
    critical_points = sdd_ai_insights.get("critical_points", [])
    if not critical_points:
        return "No se detectaron puntos criticos."

    return "\n".join(f"- {item}" for item in critical_points)


def _generate_flow_visual_placeholder():
    return "_No se genero una imagen del flujo para esta ejecucion._"


def _generate_toc(project_data):
    tasks = project_data.get("tasks", [])
    task_names = [task.get("name", "Taskbot") for task in tasks]

    lines = [
        "1. [Informacion General](#1-informacion-general)",
        "2. [Resumen Ejecutivo](#2-resumen-ejecutivo)",
        "3. [Estadisticas del Proyecto](#3-estadisticas-del-proyecto)",
        "4. [Flujo Principal Entre Taskbots](#4-flujo-principal-entre-taskbots)",
        "5. [Contrato de Dependencias](#5-contrato-de-dependencias)",
        "6. [Inventario de Taskbots](#6-inventario-de-taskbots)",
    ]
    for index, name in enumerate(task_names, start=1):
        anchor = name.lower().replace(" ", "-")
        lines.append(f"   - [{name}](#{index}-{anchor})")
    lines.extend([
        "7. [Contrato de Variables](#7-contrato-de-variables)",
        "8. [Credenciales y Vaults](#8-credenciales-y-vaults)",
        "9. [Sistemas Externos y Configuracion Tecnica](#9-sistemas-externos-y-configuracion-tecnica)",
        "10. [Paquetes AA360 Detectados](#10-paquetes-aa360-detectados)",
        "11. [Puntos Criticos del Bot](#11-puntos-criticos-del-bot)",
        "12. [Estructura del Proyecto](#12-estructura-del-proyecto)",
    ])
    return "\n".join(lines)


def _generate_dependency_contracts(tasks):
    contracts = []
    for task in tasks:
        task_calls = task.get("task_calls", [])
        if not task_calls:
            continue
        for call in task_calls:
            target = call.get("target_name", "subtask")
            inputs = call.get("inputs", [])
            outputs = call.get("outputs", [])
            contracts.append({
                "caller": task.get("name", "Taskbot"),
                "target": target,
                "inputs": inputs,
                "outputs": outputs,
            })

    if not contracts:
        return "No se detectaron invocaciones `runTask` entre taskbots."

    sections = []
    for contract in contracts:
        sections.append(f"### {contract['caller']} → {contract['target']}")
        sections.append("")

        if contract["inputs"]:
            sections.append("**Variables enviadas (entrada)**")
            sections.append("")
            sections.append("| Variable | Valor asignado |")
            sections.append("|----------|----------------|")
            for inp in contract["inputs"]:
                sections.append(f"| {inp.get('name', '-')} | {inp.get('value', '-') or '-'} |")
            sections.append("")
        else:
            sections.append("_Sin variables de entrada._")
            sections.append("")

        if contract["outputs"]:
            sections.append("**Variables recibidas (salida)**")
            sections.append("")
            sections.append("| Variable destino | Variable origen |")
            sections.append("|------------------|-----------------|")
            for out in contract["outputs"]:
                sections.append(f"| {out.get('name', '-')} | {out.get('value', '-') or '-'} |")
            sections.append("")
        else:
            sections.append("_Sin variables de salida._")
            sections.append("")

    return "\n".join(sections).rstrip()


def _generate_quality_observations(project_data):
    """Genera observaciones de calidad como documento independiente."""
    tasks = project_data.get("tasks", [])
    project_name = project_data.get("name", "Proyecto")
    observations = []
    task_descriptions = build_quality_task_descriptions(tasks)

    # Nodos deshabilitados
    for task in tasks:
        disabled = task.get("node_stats", {}).get("disabled_nodes", 0)
        if disabled > 0:
            observations.append(
                f"⚠ **{task['name']}** tiene {disabled} nodo(s) deshabilitado(s). "
                "Codigo muerto puede dificultar el mantenimiento."
            )

    # Sin manejo de errores
    for task in tasks:
        eh = task.get("error_handling", {})
        if not eh.get("has_try") and task.get("type") == "taskbot":
            observations.append(
                f"⚠ **{task['name']}** no tiene bloques try/catch. "
                "Se recomienda manejo de errores explicito."
            )

    # Try sin catch
    for task in tasks:
        eh = task.get("error_handling", {})
        if eh.get("has_try") and not eh.get("has_catch"):
            observations.append(
                f"⚠ **{task['name']}** tiene `try` pero no `catch`. "
                "Los errores no seran capturados."
            )

    # Sin descripcion
    for task in tasks:
        if not task.get("description") and task.get("type") == "taskbot":
            observations.append(
                f"ℹ **{task['name']}** no tiene descripcion declarada en cabecera."
            )

    # Sin developer
    for task in tasks:
        if not task.get("developer") and task.get("type") == "taskbot":
            observations.append(
                f"ℹ **{task['name']}** no tiene developer declarado en cabecera."
            )

    # Rutas hardcodeadas (no expresiones AA360)
    for task in tasks:
        for system in task.get("systems", []):
            value = system.get("value", "")
            if system["type"] == "file" and not value.startswith("file://$") and "$" not in value:
                observations.append(
                    f"⚠ **{task['name']}** usa ruta de archivo hardcodeada: `{value}`. "
                    "Considere usar variables globales."
                )

    # Credenciales no detectadas pero hay conexiones DB
    credentials = project_data.get("credentials", [])
    systems = project_data.get("systems", [])
    has_db = any(s["type"] == "database" for s in systems)
    if has_db and not credentials:
        observations.append(
            "⚠ Se detectaron conexiones a base de datos pero no se encontraron "
            "credenciales via CredentialVault. Verifique que las credenciales "
            "no estan hardcodeadas en las cadenas de conexion."
        )

    if not observations:
        body = "No se detectaron observaciones relevantes. El bot cumple las buenas practicas basicas."
    else:
        body = "\n".join(f"- {obs}" for obs in observations)

    interpretation_section = _generate_task_interpretation_section(tasks, task_descriptions)
    prioritization = build_quality_prioritization(project_data, task_descriptions, observations)
    priority_section = _generate_priority_findings_section(prioritization)
    sprint_plan_section = _generate_sprint_plan_section(prioritization)

    return (
        f"# Observaciones de Calidad - {project_name}\n\n"
        f"Fecha de analisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"## Resumen\n\n"
        f"- **Taskbots analizados:** {len(tasks)}\n"
        f"- **Observaciones detectadas:** {len(observations)}\n\n"
        f"## Hallazgos\n\n"
        f"{body}\n\n"
        f"## Priorizacion Inteligente de Hallazgos\n\n"
        f"{priority_section}\n\n"
        f"## Plan de Remediacion por Sprint\n\n"
        f"{sprint_plan_section}\n\n"
        f"## Interpretacion funcional por Taskbot\n\n"
        f"{interpretation_section}\n\n"
        f"---\n"
        f"Documento generado automaticamente por RPA-Doc-Generator.\n"
    )


def _generate_priority_findings_section(prioritization):
    findings = prioritization.get("priority_findings", [])
    source = prioritization.get("source", "heuristic")
    confidence = prioritization.get("confidence", "media")

    if not findings:
        return "No se detectaron hallazgos priorizables."

    lines = [
        f"- **Fuente de priorizacion:** {source}",
        f"- **Confianza estimada:** {confidence}",
        "",
        "| Severidad | Taskbot | Hallazgo | Por que importa |",
        "|-----------|---------|----------|------------------|",
    ]

    for finding in findings:
        lines.append(
            f"| {finding.get('severity', 'medio')} | {finding.get('task', 'General')} | "
            f"{finding.get('title', 'Hallazgo')} | {finding.get('why', 'Sin detalle')} |"
        )

    return "\n".join(lines)


def _generate_sprint_plan_section(prioritization):
    sprint_plan = prioritization.get("sprint_plan", [])
    if not sprint_plan:
        return "No se genero plan de remediacion."

    lines = [
        "| Prioridad | Accion | Esfuerzo | Impacto | Owner | Taskbots | Criterio de cierre |",
        "|-----------|--------|----------|---------|-------|----------|--------------------|",
    ]

    for item in sprint_plan:
        tasks = item.get("tasks", [])
        done_criteria = item.get("done_criteria", [])
        tasks_value = ", ".join(tasks) if tasks else "General"
        done_criteria_value = "<br>".join(done_criteria) if done_criteria else "Sin criterio definido"
        lines.append(
            f"| {item.get('priority', 'P2')} | {item.get('action', 'Accion pendiente')} | "
            f"{item.get('effort', 'M')} | {item.get('impact', 'Impacto pendiente')} | "
            f"{item.get('owner', 'dev')} | {tasks_value} | {done_criteria_value} |"
        )

    return "\n".join(lines)


def _generate_task_interpretation_section(tasks, task_descriptions):
    taskbots = [task for task in tasks if task.get("type") == "taskbot"]
    if not taskbots:
        return "No se detectaron taskbots para interpretar."

    lines = []
    for task in taskbots:
        task_name = task.get("name", "Taskbot")
        description = task_descriptions.get(task_name, {})
        risks = description.get("risks", ["Sin riesgos relevantes inferidos."])
        recommendations = description.get("recommendations", ["Sin recomendaciones adicionales."])

        lines.append(f"### {task_name}")
        lines.append("")
        lines.append(f"- **Perfil AA360 sugerido:** {description.get('task_profile', 'utilitario')}")
        lines.append(f"- **Que hace:** {description.get('what_it_does', 'No disponible')}")
        lines.append(f"- **Funcion que cumple:** {description.get('business_function', 'No disponible')}")
        lines.append(f"- **Criticidad estimada:** {description.get('criticality', 'media')}")
        lines.append("- **Riesgos detectados:**")
        lines.extend(f"  - {risk}" for risk in risks)
        lines.append("- **Mejoras recomendadas:**")
        lines.extend(f"  - {recommendation}" for recommendation in recommendations)
        lines.append(f"- **Fuente de analisis:** {description.get('source', 'heuristic')}")
        lines.append(f"- **Confianza estimada:** {description.get('confidence', 'media')}")
        lines.append("")

    return "\n".join(lines).rstrip()


def generate_quality_file(project_data, output_path):
    """Genera el reporte de calidad y lo guarda en un archivo."""
    try:
        content = _generate_quality_observations(project_data)
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as file_obj:
            file_obj.write(content)

        logger.info("Reporte de calidad guardado en: %s", output_file)
        return str(output_file)
    except Exception as exc:
        logger.error("Error guardando reporte de calidad: %s", exc)
        raise


def _describe_error_handling(error_handling):
    states = []
    if error_handling.get("has_try"):
        states.append("try")
    if error_handling.get("has_catch"):
        states.append("catch")
    if error_handling.get("has_finally"):
        states.append("finally")
    return ", ".join(states) if states else "No explicito"


def _unique_preserve(values):
    seen = set()
    unique = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


def _format_size(bytes_size):
    if bytes_size is None:
        return "0B"

    size = int(bytes_size)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def _generate_default_template():
    return """# SDD - {name}

## Tabla de Contenido
{toc}

## 1. Informacion General
{overview}

## 2. Resumen Ejecutivo
{executive_summary}

## 3. Estadisticas del Proyecto
{statistics}

## 4. Flujo Principal Entre Taskbots
{flow_visual}

## 5. Contrato de Dependencias
{dependency_contracts}

## 6. Inventario de Taskbots
{task_inventory}

## 7. Contrato de Variables
{variables_section}

## 8. Credenciales y Vaults
{credentials_section}

## 9. Sistemas Externos y Configuracion Tecnica
{systems_section}

## 10. Paquetes AA360 Detectados
{packages_section}

## 11. Puntos Criticos del Bot
{critical_points}

## 12. Estructura del Proyecto
```
{tree}
```

---
Documento generado automaticamente por RPA-Doc-Generator el {generated_date}.
"""
