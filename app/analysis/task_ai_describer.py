import json
import logging
import re
from urllib import request, error

from app.application.settings import AppSettings

logger = logging.getLogger(__name__)


def describe_task_with_ai(task, settings=None):
    """
    Describe functional intent and quality-oriented insights for one taskbot.

    Returns:
        dict with keys: task_profile, what_it_does, business_function,
        criticality, risks, recommendations, confidence, source
    """
    runtime_settings = settings or AppSettings.from_env()

    if not _is_ai_enabled(runtime_settings):
        return _heuristic_description(task)

    provider_config = _resolve_ai_provider_config(runtime_settings)
    api_key = provider_config["api_key"]
    if not api_key:
        logger.info("AI quality enabled but provider API key is missing. Using heuristic fallback.")
        return _heuristic_description(task)

    model = provider_config["model"]
    base_url = provider_config["base_url"]
    timeout = _safe_timeout(runtime_settings.ai_timeout_seconds)

    prompt = _build_prompt(task)
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un analista tecnico de Automation Anywhere enfocado en calidad. "
                    "Debes inferir proposito funcional del taskbot, su funcion en el flujo, criticidad, "
                    "riesgos y mejoras. Responde unicamente JSON valido."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }

    endpoint = f"{base_url}/chat/completions"

    try:
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")

        data = json.loads(raw)
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        parsed = _extract_model_json(content)
        if not parsed:
            logger.warning("AI response could not be parsed as JSON. Using heuristic fallback.")
            return _heuristic_description(task)

        return {
            "task_profile": _normalize_task_profile(parsed.get("task_profile")),
            "what_it_does": str(parsed.get("what_it_does", "")).strip() or "No disponible",
            "business_function": str(parsed.get("business_function", "")).strip() or "No disponible",
            "criticality": _normalize_level(parsed.get("criticality"), default="media"),
            "risks": _normalize_list(parsed.get("risks"), default_message="Sin riesgos relevantes inferidos."),
            "recommendations": _normalize_list(
                parsed.get("recommendations"),
                default_message="Sin recomendaciones adicionales.",
            ),
            "confidence": _normalize_level(parsed.get("confidence"), default="media"),
            "source": "ai",
        }

    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("AI describe call failed: %s. Using heuristic fallback.", exc)
        return _heuristic_description(task)
    except Exception as exc:
        logger.warning("Unexpected error while describing task with AI: %s", exc)
        return _heuristic_description(task)


def build_quality_task_descriptions(tasks, settings=None):
    descriptions = {}
    for task in tasks:
        if task.get("type") != "taskbot":
            continue
        descriptions[task.get("name", "Taskbot")] = describe_task_with_ai(task, settings=settings)
    return descriptions


def classify_task_for_aa360(task):
    return _infer_task_profile(task)


def build_sdd_ai_insights(project_data, flow=None, settings=None):
    """
    Build AI-enhanced SDD insights.

    Returns:
        dict with keys: executive_summary, critical_points, source, confidence
    """
    runtime_settings = settings or AppSettings.from_env()

    if not _is_ai_enabled(runtime_settings):
        return _heuristic_sdd_insights(project_data, flow)

    provider_config = _resolve_ai_provider_config(runtime_settings)
    api_key = provider_config["api_key"]
    if not api_key:
        return _heuristic_sdd_insights(project_data, flow)

    model = provider_config["model"]
    base_url = provider_config["base_url"]
    timeout = _safe_timeout(runtime_settings.ai_timeout_seconds)

    prompt = _build_sdd_prompt(project_data, flow)
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un arquitecto tecnico de RPA. Genera resumen ejecutivo y puntos criticos "
                    "claros para devs que deben entender y mantener el bot. Responde solo JSON valido."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }

    endpoint = f"{base_url}/chat/completions"
    try:
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")

        data = json.loads(raw)
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        parsed = _extract_model_json(content)
        if not parsed:
            return _heuristic_sdd_insights(project_data, flow)

        return {
            "executive_summary": _normalize_list(
                parsed.get("executive_summary"),
                default_message="No se pudo generar resumen ejecutivo.",
            )[:8],
            "critical_points": _normalize_list(
                parsed.get("critical_points"),
                default_message="No se detectaron puntos criticos relevantes.",
            )[:8],
            "source": "ai",
            "confidence": _normalize_level(parsed.get("confidence"), default="media"),
        }
    except Exception:
        return _heuristic_sdd_insights(project_data, flow)


def build_quality_prioritization(project_data, task_descriptions, observations, settings=None):
    """
    Build prioritized findings and a sprint remediation plan.

    Returns:
        dict with keys: priority_findings, sprint_plan, source, confidence
    """
    runtime_settings = settings or AppSettings.from_env()

    if not _is_ai_enabled(runtime_settings):
        return _heuristic_prioritization(task_descriptions, observations)

    provider_config = _resolve_ai_provider_config(runtime_settings)
    api_key = provider_config["api_key"]
    if not api_key:
        return _heuristic_prioritization(task_descriptions, observations)

    model = provider_config["model"]
    base_url = provider_config["base_url"]
    timeout = _safe_timeout(runtime_settings.ai_timeout_seconds)

    prompt = _build_prioritization_prompt(project_data, task_descriptions, observations)
    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un tech lead de RPA. Priorizas riesgos para ejecucion real y propones plan por sprint. "
                    "Responde solo JSON valido."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }

    endpoint = f"{base_url}/chat/completions"
    try:
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")

        data = json.loads(raw)
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        parsed = _extract_model_json(content)
        if not parsed:
            return _heuristic_prioritization(task_descriptions, observations)

        return {
            "priority_findings": _normalize_priority_findings(parsed.get("priority_findings", [])),
            "sprint_plan": _normalize_sprint_plan(parsed.get("sprint_plan", [])),
            "source": "ai",
            "confidence": _normalize_level(parsed.get("confidence"), default="media"),
        }
    except Exception:
        return _heuristic_prioritization(task_descriptions, observations)


def _is_ai_enabled(settings):
    return bool(settings.ai_quality_enabled)


def _resolve_ai_provider_config(settings):
    groq_api_key = settings.groq_api_key
    if groq_api_key:
        return {
            "provider": "groq",
            "api_key": groq_api_key,
            "model": settings.groq_model,
            "base_url": settings.groq_base_url,
        }

    return {
        "provider": "openai-compatible",
        "api_key": settings.openai_api_key,
        "model": settings.openai_model,
        "base_url": settings.openai_base_url,
    }


def _safe_timeout(value):
    try:
        timeout = int(value)
        return timeout if timeout > 0 else 25
    except (TypeError, ValueError):
        return 25


def _build_prompt(task):
    compact_task = {
        "name": task.get("name", "Taskbot"),
        "role": task.get("role", "taskbot"),
        "suggested_task_profile": _infer_task_profile(task),
        "description_declared": task.get("description", ""),
        "actions": task.get("actions", [])[:12],
        "comments": task.get("comments", [])[:8],
        "task_calls": [call.get("target_name", "") for call in task.get("task_calls", [])[:8]],
        "systems": [{"type": s.get("type", ""), "value": s.get("value", "")} for s in task.get("systems", [])[:8]],
        "dependencies": [
            {"name": item.get("name", ""), "type": item.get("type", "")}
            for item in task.get("dependencies", [])[:8]
        ],
        "packages": [
            {"name": package.get("name", ""), "version": package.get("version", "")}
            for package in task.get("packages", [])[:8]
        ],
        "triggers": [trigger.get("type", "") for trigger in task.get("triggers", [])[:5]],
        "credentials": [
            {
                "credential_name": item.get("credential_name", ""),
                "vault": item.get("vault", ""),
            }
            for item in task.get("credentials", [])[:5]
        ],
        "variables": {
            "input": len(task.get("variables", {}).get("input", [])),
            "output": len(task.get("variables", {}).get("output", [])),
            "internal": len(task.get("variables", {}).get("internal", [])),
        },
        "node_stats": task.get("node_stats", {}),
        "error_handling": task.get("error_handling", {}),
    }

    instructions = (
        "Eres un code reviewer senior de Automation Anywhere 360 (AA360). "
        "Interpreta taskbots, runTask, Credential Vault, packages, triggers y contratos de variables como conceptos nativos de AA360. "
        "Tambien clasifica cada taskbot en uno de estos perfiles AA360: principal, utilitario, integracion, validacion. "
        "Devuelve JSON claro y practico, como mensajes para devs, no para reportes formales. Usa lenguaje directo y corto. "
        "Riesgos: que puede romper. Recomendaciones: que hacer. "
        "Devuelve solo JSON con esta forma: "
        "{\"task_profile\":\"principal|utilitario|integracion|validacion\", \"what_it_does\":\"...\", \"business_function\":\"...\", \"criticality\":\"alta|media|baja\", "
        "\"risks\":[\"...\"], \"recommendations\":[\"...\"], \"confidence\":\"alta|media|baja\"}. "
        "Sin markdown. Solo JSON valido."
    )
    return f"{instructions}\n\nTaskbot:\n{json.dumps(compact_task, ensure_ascii=True)}"


def _build_sdd_prompt(project_data, flow):
    tasks = project_data.get("tasks", [])
    summary = {
        "project": project_data.get("name", "Proyecto"),
        "description": project_data.get("metadata", {}).get("description", ""),
        "entrypoints": project_data.get("metadata", {}).get("entrypoints", []),
        "task_count": len(tasks),
        "systems": [item.get("type", "") for item in project_data.get("systems", [])[:10]],
        "packages": [item.get("name", "") for item in project_data.get("packages", [])[:10]],
        "credentials_count": len(project_data.get("credentials", [])),
        "flow_edges": (flow or {}).get("summary", {}).get("total_edges", 0),
        "tasks": [
            {
                "name": task.get("name", "Taskbot"),
                "role": task.get("role", "taskbot"),
                "entrypoint": task.get("is_entrypoint", False),
                "actions": task.get("actions", [])[:5],
                "task_calls": [call.get("target_name", "") for call in task.get("task_calls", [])[:5]],
                "dependencies": [item.get("name", "") for item in task.get("dependencies", [])[:5]],
                "systems": [system.get("type", "") for system in task.get("systems", [])[:5]],
                "packages": [package.get("name", "") for package in task.get("packages", [])[:5]],
                "triggers": [trigger.get("type", "") for trigger in task.get("triggers", [])[:5]],
                "credentials": [item.get("credential_name", "") for item in task.get("credentials", [])[:5]],
                "error_handling": task.get("error_handling", {}),
                "node_stats": task.get("node_stats", {}),
            }
            for task in tasks[:12]
        ],
    }

    instructions = (
        "Analiza este export de Automation Anywhere 360 (AA360). "
        "Trata taskbots, runTask, Credential Vault, packages, triggers y variables como elementos propios del producto. "
        "Devuelve solo JSON con esta forma exacta: "
        '{"executive_summary":["..."],"critical_points":["..."],"confidence":"alta|media|baja"}. '
        "El resumen ejecutivo debe explicar que hace el bot, que sistemas toca y como fluye a alto nivel. "
        "Los puntos criticos deben enfocarse en mantenimiento, dependencias, errores y partes fragiles. "
        "Usa lenguaje claro para devs. Maximo 8 bullets por lista."
    )
    return f"{instructions}\n\nContexto:\n{json.dumps(summary, ensure_ascii=True)}"


def _build_prioritization_prompt(project_data, task_descriptions, observations):
    summary = {
        "project": project_data.get("name", "Proyecto"),
        "task_count": len(project_data.get("tasks", [])),
        "entrypoints": project_data.get("metadata", {}).get("entrypoints", []),
        "observations": observations[:30],
        "task_descriptions": [
            {
                "task": task_name,
                "task_profile": details.get("task_profile", "utilitario"),
                "criticality": details.get("criticality", "media"),
                "top_risks": details.get("risks", [])[:3],
                "top_recommendations": details.get("recommendations", [])[:3],
            }
            for task_name, details in task_descriptions.items()
        ],
    }

    instructions = (
        "Analiza los hallazgos como un proyecto de Automation Anywhere 360 (AA360). "
        "Prioriza lo que puede romper taskbots, runTask, variables, triggers, Credential Vault o integraciones. "
        "Devuelve solo JSON con esta forma exacta: "
        '{"priority_findings":[{"severity":"bloqueante|alto|medio|bajo","title":"...","why":"...","task":"..."}],'
        '"sprint_plan":[{"priority":"P1|P2|P3","action":"...","effort":"S|M|L","impact":"...","owner":"dev|qa|rpa-lead","tasks":["..."],"done_criteria":["..."]}],'
        '"confidence":"alta|media|baja"}. '
        "Maximo 6 findings y 6 acciones. Prioriza lo que puede romper produccion."
    )
    return f"{instructions}\n\nContexto:\n{json.dumps(summary, ensure_ascii=True)}"


def _extract_model_json(content):
    if not content:
        return None

    raw = content.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _normalize_level(value, default="media"):
    normalized = str(value or default).strip().lower()
    if normalized in {"alta", "media", "baja"}:
        return normalized
    return default


def _normalize_task_profile(value):
    normalized = str(value or "utilitario").strip().lower()
    if normalized in {"principal", "utilitario", "integracion", "validacion"}:
        return normalized
    return "utilitario"


def _normalize_severity(value):
    normalized = str(value or "medio").strip().lower()
    if normalized in {"bloqueante", "alto", "medio", "bajo"}:
        return normalized
    return "medio"


def _normalize_effort(value):
    normalized = str(value or "M").strip().upper()
    if normalized in {"S", "M", "L"}:
        return normalized
    return "M"


def _normalize_priority(value):
    normalized = str(value or "P2").strip().upper()
    if normalized in {"P1", "P2", "P3"}:
        return normalized
    return "P2"



def _normalize_list(value, default_message):
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or [default_message]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return [default_message]


def _normalize_priority_findings(findings):
    if not isinstance(findings, list):
        return []

    normalized = []
    for finding in findings[:6]:
        if not isinstance(finding, dict):
            continue
        title = str(
            finding.get("title")
            or finding.get("hallazgo")
            or finding.get("finding")
            or "Hallazgo sin titulo"
        ).strip()
        why = str(
            finding.get("why")
            or finding.get("why_it_matters")
            or finding.get("reason")
            or "Sin justificacion"
        ).strip()
        task = str(
            finding.get("task")
            or finding.get("taskbot")
            or finding.get("task_name")
            or "General"
        ).strip()
        normalized.append(
            {
                "severity": _normalize_severity(finding.get("severity")),
                "title": title,
                "why": why,
                "task": task,
            }
        )
    return normalized


def _normalize_sprint_plan(plan):
    if not isinstance(plan, list):
        return []

    normalized = []
    for action in plan[:6]:
        if not isinstance(action, dict):
            continue
        tasks = action.get("tasks", [])
        done_criteria = action.get("done_criteria", [])
        if isinstance(tasks, str):
            tasks = [tasks]
        if isinstance(done_criteria, str):
            done_criteria = [done_criteria]
        if not isinstance(tasks, list):
            tasks = []
        if not isinstance(done_criteria, list):
            done_criteria = []

        normalized.append(
            {
                "priority": _normalize_priority(action.get("priority")),
                "action": str(action.get("action", "Accion no especificada")).strip(),
                "effort": _normalize_effort(action.get("effort")),
                "impact": str(action.get("impact", "Impacto no especificado")).strip(),
                "owner": str(action.get("owner", "dev")).strip(),
                "tasks": [str(task).strip() for task in tasks if str(task).strip()],
                "done_criteria": [
                    str(item).strip() for item in done_criteria if str(item).strip()
                ]
                or ["Validado en QA y sin errores en ejecucion de prueba."],
            }
        )
    return normalized


def _heuristic_prioritization(task_descriptions, observations):
    findings = []
    for task_name, description in task_descriptions.items():
        criticality = description.get("criticality", "media")
        task_profile = description.get("task_profile", "utilitario")
        if criticality == "alta":
            findings.append(
                {
                    "severity": "alto",
                    "title": f"Taskbot critico: {task_name}",
                    "why": f"Tiene alta criticidad y perfil {task_profile}; puede afectar ejecucion end-to-end.",
                    "task": task_name,
                }
            )

    for observation in observations[:6]:
        severity = "medio"
        text = str(observation)
        lowered = text.lower()
        if "no tiene bloques try/catch" in lowered or "try` pero no `catch" in lowered:
            severity = "bloqueante"
        elif "credenciales" in lowered or "hardcode" in lowered:
            severity = "alto"

        findings.append(
            {
                "severity": severity,
                "title": _build_priority_finding_title(text),
                "why": re.sub(r"[*`]+", "", text)[:220],
                "task": _extract_task_name_from_observation(text),
            }
        )

    findings = _sort_findings_by_severity(findings)[:6]

    sprint_plan = []
    if any(f["severity"] == "bloqueante" for f in findings):
        sprint_plan.append(
            {
                "priority": "P1",
                "action": "Agregar o corregir try/catch en taskbots criticos.",
                "effort": "M",
                "impact": "Reduce caidas del flujo por excepciones no controladas.",
                "owner": "dev",
                "tasks": _top_tasks_from_findings(findings, limit=3),
                "done_criteria": [
                    "Taskbots criticos ejecutan con try/catch activo.",
                    "Errores quedan logueados con contexto util.",
                    "QA valida corrida completa sin interrupciones por excepcion.",
                ],
            }
        )

    if any("credencial" in f["why"].lower() or "hardcode" in f["why"].lower() for f in findings):
        sprint_plan.append(
            {
                "priority": "P1",
                "action": "Eliminar secretos/rutas hardcodeadas y moverlos a vault o variables.",
                "effort": "M",
                "impact": "Disminuye riesgo de seguridad y cambios manuales por ambiente.",
                "owner": "dev",
                "tasks": _top_tasks_from_findings(findings, limit=3),
                "done_criteria": [
                    "No hay credenciales en texto plano en taskbots.",
                    "Rutas sensibles usan variables o config por ambiente.",
                    "QA valida ejecucion en al menos dos ambientes.",
                ],
            }
        )

    sprint_plan.append(
        {
            "priority": "P2",
            "action": "Documentar cabeceras y contratos de subtareas en taskbots con mayor acoplamiento.",
            "effort": "S",
            "impact": "Mejora mantenibilidad y acelera debugging.",
            "owner": "rpa-lead",
            "tasks": _top_tasks_from_findings(findings, limit=4),
            "done_criteria": [
                "Cada taskbot objetivo tiene descripcion funcional y owner.",
                "Contrato de variables input/output documentado por subtarea.",
            ],
        }
    )

    return {
        "priority_findings": findings,
        "sprint_plan": sprint_plan[:6],
        "source": "heuristic",
        "confidence": "media",
    }


def _heuristic_sdd_insights(project_data, flow):
    tasks = project_data.get("tasks", [])
    metadata = project_data.get("metadata", {})
    systems = project_data.get("systems", [])
    entrypoints = metadata.get("entrypoints", [])
    flow_edges = (flow or {}).get("summary", {}).get("total_edges", 0)
    main_tasks = [task.get("name", "Taskbot") for task in tasks if task.get("is_entrypoint")][:3]
    task_calls = sum(len(task.get("task_calls", [])) for task in tasks)
    tasks_without_error_handling = [
        task.get("name", "Taskbot")
        for task in tasks
        if task.get("type") == "taskbot" and not task.get("error_handling", {}).get("has_try")
    ]
    external_types = sorted({system.get("type", "desconocido") for system in systems if system.get("type")})
    profiles = [classify_task_for_aa360(task) for task in tasks if task.get("type") == "taskbot"]
    profile_summary = _summarize_profiles(profiles)

    executive_summary = [
        (
            f"El bot {project_data.get('name', 'Proyecto')} automatiza un flujo de {len(tasks)} taskbot(s) "
            f"con entrada principal en {', '.join(entrypoints) if entrypoints else 'taskbots no identificados'}"
        ),
        (
            f"El proceso conecta {len(external_types)} tipo(s) de sistema externo: "
            f"{', '.join(external_types) if external_types else 'sin integraciones detectadas'}"
        ),
        (
            f"La orquestacion principal pasa por {', '.join(main_tasks) if main_tasks else 'taskbots sin entrypoint claro'} "
            f"y registra {flow_edges} relacion(es) entre taskbots"
        ),
        (
            f"Perfiles AA360 sugeridos en el bot: {profile_summary}"
        ),
        (
            f"En total se detectaron {task_calls} llamada(s) a subtareas, por lo que el comportamiento depende "
            "de contratos bien definidos entre taskbots"
        ),
    ]

    critical_points = []
    if tasks_without_error_handling:
        critical_points.append(
            f"Revisar manejo de errores en: {', '.join(tasks_without_error_handling[:5])}; hoy pueden cortar el flujo sin recuperacion clara"
        )
    if external_types:
        critical_points.append(
            f"Las integraciones externas ({', '.join(external_types)}) son puntos fragiles; si cambian respuestas o credenciales, el bot falla"
        )
    if task_calls > 0:
        critical_points.append(
            "Las llamadas entre taskbots requieren contratos estables de variables; un cambio en nombres o outputs puede romper el flujo completo"
        )

    disabled_total = sum(task.get("node_stats", {}).get("disabled_nodes", 0) for task in tasks)
    if disabled_total:
        critical_points.append(
            f"Hay {disabled_total} nodo(s) deshabilitado(s); conviene limpiarlos o documentarlos para evitar falsas pistas al mantener el bot"
        )

    if not critical_points:
        critical_points.append("No se detectaron puntos criticos estructurales fuera de lo esperado para el bot analizado")

    return {
        "executive_summary": executive_summary[:8],
        "critical_points": critical_points[:8],
        "source": "heuristic",
        "confidence": "media",
    }


def _sort_findings_by_severity(findings):
    order = {"bloqueante": 0, "alto": 1, "medio": 2, "bajo": 3}
    return sorted(findings, key=lambda item: order.get(item.get("severity", "medio"), 2))


def _extract_task_name_from_observation(observation):
    match = re.search(r"\*\*(.+?)\*\*", str(observation))
    if match:
        return match.group(1)
    return "General"


def _build_priority_finding_title(observation):
    text = str(observation)
    lowered = text.lower()

    if "try/catch" in lowered:
        return "Manejo de errores incompleto"
    if "hardcode" in lowered:
        return "Ruta o valor hardcodeado"
    if "credentialvault" in lowered or "credenciales" in lowered:
        return "Riesgo de credenciales fuera de vault"
    if "deshabilitado" in lowered:
        return "Nodos deshabilitados sin depurar"
    if "descripcion declarada" in lowered:
        return "Falta descripcion funcional"
    if "developer declarado" in lowered:
        return "Falta owner tecnico"

    cleaned = re.sub(r"[*`]+", "", text).strip(" -:.\n\t")
    if not cleaned:
        return "Hallazgo detectado"

    return cleaned[:72] + "..." if len(cleaned) > 72 else cleaned


def _top_tasks_from_findings(findings, limit):
    tasks = []
    for finding in findings:
        task = finding.get("task", "General")
        if not task or task == "General" or task in tasks:
            continue
        tasks.append(task)
        if len(tasks) >= limit:
            break
    return tasks



def _infer_criticality(task):
    """Calcula criticidad (alta|media|baja) basada en complejidad, sistemas externos y error handling."""
    score = 0
    systems = task.get("systems", [])
    task_calls = task.get("task_calls", [])
    node_stats = task.get("node_stats", {})
    error_handling = task.get("error_handling", {})

    score += min(len(systems), 3)
    score += min(len(task_calls), 3)
    score += 1 if node_stats.get("decision_nodes", 0) > 0 else 0
    score += 1 if node_stats.get("loop_nodes", 0) > 0 else 0
    score += 1 if node_stats.get("total_nodes", 0) >= 15 else 0
    score += 1 if error_handling.get("has_try") and not error_handling.get("has_catch") else 0

    if score >= 5:
        return "alta"
    if score >= 2:
        return "media"
    return "baja"


def _infer_task_profile(task):
    name = str(task.get("name", "")).lower()
    role = str(task.get("role", "")).lower()
    systems = task.get("systems", [])
    task_calls = task.get("task_calls", [])
    actions = " ".join(str(action).lower() for action in task.get("actions", []))
    comments = " ".join(str(comment).lower() for comment in task.get("comments", []))

    if task.get("is_entrypoint") or role == "main" or name == "main":
        return "principal"

    integration_types = {"url", "database", "file"}
    if any(system.get("type") in integration_types for system in systems):
        return "integracion"

    validation_terms = {
        "valida", "validacion", "validate", "validation", "ofac", "check", "verifica", "verify"
    }
    if any(term in actions or term in comments or term in name for term in validation_terms):
        return "validacion"

    if not task_calls and len(systems) == 0:
        return "utilitario"

    return "utilitario"


def _summarize_profiles(profiles):
    if not profiles:
        return "sin clasificacion disponible"

    counts = {}
    for profile in profiles:
        counts[profile] = counts.get(profile, 0) + 1
    return ", ".join(f"{count} {profile}" for profile, count in sorted(counts.items()))



def _heuristic_description(task):
    """Genera descripción local sin IA cuando ésta no está habilitada o falla."""
    name = task.get("name", "Taskbot")
    actions = [str(action).strip() for action in task.get("actions", []) if str(action).strip()]
    comments = [str(comment).strip() for comment in task.get("comments", []) if str(comment).strip()]
    task_calls = [call.get("target_name", "") for call in task.get("task_calls", []) if call.get("target_name")]
    systems = task.get("systems", [])
    node_stats = task.get("node_stats", {})
    error_handling = task.get("error_handling", {})

    action_hint = actions[0] if actions else "ejecucion de pasos de automatizacion"
    comment_hint = comments[0] if comments else "sin comentario funcional explicito"

    systems_by_type = {}
    for system in systems:
        system_type = system.get("type", "desconocido")
        systems_by_type[system_type] = systems_by_type.get(system_type, 0) + 1

    if systems_by_type:
        systems_summary = ", ".join(f"{count} {stype}" for stype, count in sorted(systems_by_type.items()))
    else:
        systems_summary = "sin sistemas externos detectados"

    if task_calls:
        calls_summary = f"Coordina subtareas: {', '.join(task_calls[:4])}"
    else:
        calls_summary = "No invoca subtareas de forma explicita"

    criticality = _infer_criticality(task)
    risks = []
    recommendations = []

    if systems:
        system_types = set(s.get("type", "") for s in systems)
        risks.append(f"Usa {', '.join(system_types)}: si alguno no responde, esta tarea falla.")
    if task_calls:
        num_calls = len(task_calls)
        risks.append(f"Llama {num_calls} subtarea(s): si alguna rompe, todo se detiene.")
    if error_handling.get("has_try") and not error_handling.get("has_catch"):
        risks.append("Try sin catch: los errores no se controlan, pueden quedar ocultos.")
    if not error_handling.get("has_try"):
        risks.append("Sin try/catch: un error aqui detiene el flujo y nadie sabe por que.")
    if node_stats.get("disabled_nodes", 0) > 0:
        num_disabled = node_stats.get("disabled_nodes", 0)
        risks.append(f"Tiene {num_disabled} nodo(s) deshabilitado(s): limpialos o documenta por que estan.")
    if not risks:
        risks.append("No se detectaron riesgos estructurales significativos.")

    if not task.get("description"):
        recommendations.append("Escribe un comentario en la cabecera: que hace, quien la usa, cuando entra en juego.")
    if not task.get("developer"):
        recommendations.append("Pon tu nombre en la cabecera (Developer: tu_nombre) para que sepamos a quien preguntar.")
    if not error_handling.get("has_try"):
        recommendations.append("Agrega try/catch alrededor de pasos criticos. Despues decide: reintentar, loguear, o fallar limpiamente.")
    if task_calls:
        recommendations.append("Documenta el contrato: que variables esperas de cada subtarea y cuales les pasas.")
    if not recommendations:
        recommendations.append("Mantener testing y monitoreo en linea con la responsabilidad de esta tarea.")

    return {
        "task_profile": _infer_task_profile(task),
        "what_it_does": (
            f"{name} parece ejecutar {action_hint}; contexto detectado: {comment_hint}. "
            f"Interacciona con {systems_summary}."
        ),
        "business_function": calls_summary,
        "criticality": criticality,
        "risks": risks,
        "recommendations": recommendations,
        "confidence": "media",
        "source": "heuristic",
    }
