import json
import os
import unittest
from unittest.mock import patch

from app.analysis import task_ai_describer
from app.generator import sdd_generator


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TaskAIDescriberTests(unittest.TestCase):
    def setUp(self):
        self.task = {
            "name": "Main",
            "type": "taskbot",
            "role": "main",
            "description": "",
            "actions": ["Abrir portal", "Consultar OFAC"],
            "comments": ["Valida cliente"],
            "dependencies": [{"name": "Lookup", "type": "runTask"}],
            "task_calls": [{"target_name": "Lookup"}],
            "systems": [{"type": "url", "value": "https://example.com"}],
            "packages": [{"name": "Browser", "version": "1.0"}],
            "triggers": [{"type": "manual"}],
            "credentials": [{"credential_name": "AA360_LOGIN", "vault": "Default"}],
            "variables": {"input": [], "output": [], "internal": []},
            "node_stats": {"total_nodes": 3},
            "error_handling": {"has_try": False, "has_catch": False, "has_finally": False},
        }

    @patch.dict(os.environ, {}, clear=True)
    def test_describe_task_with_ai_uses_heuristic_when_disabled(self):
        result = task_ai_describer.describe_task_with_ai(self.task)
        self.assertEqual(result["source"], "heuristic")
        self.assertEqual(result["task_profile"], "principal")
        self.assertIn("Main", result["what_it_does"])
        self.assertIn("Lookup", result["business_function"])
        self.assertIn(result["criticality"], {"alta", "media", "baja"})
        self.assertTrue(result["risks"])
        self.assertTrue(result["recommendations"])

    @patch.dict(
        os.environ,
        {
            "AI_QUALITY_ENABLED": "true",
            "GROQ_API_KEY": "test-key",
            "GROQ_MODEL": "llama-3.3-70b-versatile",
            "GROQ_BASE_URL": "https://api.groq.com/openai/v1",
        },
        clear=True,
    )
    def test_describe_task_with_ai_reads_openai_response(self):
        response_payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "what_it_does": "Ejecuta validacion de clientes en listas OFAC.",
                                "business_function": "Reduce riesgo de cumplimiento regulatorio.",
                                "criticality": "alta",
                                "risks": ["Depende de un portal externo para completar la validacion."],
                                "recommendations": ["Agregar reintentos y observabilidad del portal."],
                                "confidence": "alta",
                            }
                        )
                    }
                }
            ]
        }

        with patch("app.analysis.task_ai_describer.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _FakeResponse(json.dumps(response_payload).encode("utf-8"))
            result = task_ai_describer.describe_task_with_ai(self.task)

        self.assertEqual(result["source"], "ai")
        self.assertEqual(result["confidence"], "alta")
        self.assertEqual(result["criticality"], "alta")
        self.assertEqual(len(result["risks"]), 1)
        self.assertEqual(len(result["recommendations"]), 1)
        self.assertIn("validacion de clientes", result["what_it_does"].lower())

    @patch.dict(os.environ, {}, clear=True)
    def test_quality_report_contains_task_interpretation_section(self):
        project_data = {
            "name": "DemoBot",
            "tasks": [self.task],
            "systems": [],
            "credentials": [],
        }

        report = sdd_generator._generate_quality_observations(project_data)
        self.assertIn("Interpretacion funcional por Taskbot", report)
        self.assertIn("Priorizacion Inteligente de Hallazgos", report)
        self.assertIn("Plan de Remediacion por Sprint", report)
        self.assertIn("Criterio de cierre", report)
        self.assertIn("### Main", report)
        self.assertIn("Perfil AA360 sugerido", report)
        self.assertIn("Que hace", report)
        self.assertIn("Funcion que cumple", report)
        self.assertIn("Criticidad estimada", report)
        self.assertIn("Riesgos detectados", report)
        self.assertIn("Mejoras recomendadas", report)

    @patch.dict(os.environ, {}, clear=True)
    def test_build_quality_prioritization_heuristic_returns_expected_shape(self):
        task_descriptions = {
            "Main": {
                "criticality": "alta",
                "risks": ["Sin try/catch"],
                "recommendations": ["Agregar try/catch"],
            }
        }
        observations = [
            "⚠ **Main** no tiene bloques try/catch. Se recomienda manejo de errores explicito.",
            "⚠ **Main** usa ruta de archivo hardcodeada: C:/tmp/a.txt",
        ]

        result = task_ai_describer.build_quality_prioritization(
            {"name": "DemoBot", "tasks": [self.task]},
            task_descriptions,
            observations,
        )

        self.assertIn(result["source"], {"heuristic", "ai"})
        self.assertTrue(result["priority_findings"])
        self.assertTrue(result["sprint_plan"])
        self.assertIn(result["priority_findings"][0]["severity"], {"bloqueante", "alto", "medio", "bajo"})
        self.assertTrue(result["sprint_plan"][0]["done_criteria"])

    def test_normalize_priority_findings_accepts_ai_style_keys(self):
        findings = task_ai_describer._normalize_priority_findings(
            [
                {
                    "severity": "alto",
                    "hallazgo": "Ruta hardcodeada",
                    "why_it_matters": "Genera riesgo operativo entre ambientes.",
                    "taskbot": "Main",
                }
            ]
        )

        self.assertEqual(findings, [
            {
                "severity": "alto",
                "title": "Ruta hardcodeada",
                "why": "Genera riesgo operativo entre ambientes.",
                "task": "Main",
            }
        ])

    def test_heuristic_prioritization_builds_meaningful_titles(self):
        result = task_ai_describer._heuristic_prioritization(
            {"Main": {"criticality": "media", "task_profile": "principal"}},
            [
                "⚠ **Main** no tiene bloques try/catch. Se recomienda manejo de errores explicito.",
                "⚠ **Main** usa ruta de archivo hardcodeada: C:/tmp/a.txt",
                "⚠ Se detectaron conexiones a base de datos pero no se encontraron credenciales via CredentialVault.",
            ],
        )

        titles = [finding["title"] for finding in result["priority_findings"]]
        self.assertIn("Manejo de errores incompleto", titles)
        self.assertIn("Ruta o valor hardcodeado", titles)
        self.assertIn("Riesgo de credenciales fuera de vault", titles)

    def test_prompts_include_aa360_specific_context(self):
        quality_prompt = task_ai_describer._build_prompt(self.task)
        self.assertIn("Automation Anywhere 360", quality_prompt)
        self.assertIn("principal|utilitario|integracion|validacion", quality_prompt)
        self.assertIn("Credential Vault", quality_prompt)
        self.assertIn("runTask", quality_prompt)
        self.assertIn("Browser", quality_prompt)

        sdd_prompt = task_ai_describer._build_sdd_prompt(
            {
                "name": "DemoBot",
                "metadata": {"description": "Demo", "entrypoints": ["Main"]},
                "tasks": [self.task],
                "systems": self.task["systems"],
                "packages": self.task["packages"],
                "credentials": self.task["credentials"],
            },
            {"summary": {"total_edges": 1}},
        )
        self.assertIn("Automation Anywhere 360", sdd_prompt)
        self.assertIn("Credential Vault", sdd_prompt)
        self.assertIn("triggers", sdd_prompt)

    def test_classify_task_for_aa360_distinguishes_profiles(self):
        self.assertEqual(task_ai_describer.classify_task_for_aa360(self.task), "principal")

        validation_task = dict(self.task)
        validation_task.update(
            {
                "name": "ValidarCliente",
                "role": "subtask",
                "is_entrypoint": False,
                "actions": ["Validar identidad", "Check OFAC"],
                "systems": [],
                "task_calls": [],
            }
        )
        self.assertEqual(task_ai_describer.classify_task_for_aa360(validation_task), "validacion")

        integration_task = dict(self.task)
        integration_task.update(
            {
                "name": "SyncCRM",
                "role": "subtask",
                "is_entrypoint": False,
                "actions": ["Enviar datos CRM"],
                "comments": ["Sin validacion funcional"],
                "systems": [{"type": "database", "value": "db.local"}],
                "task_calls": [],
            }
        )
        self.assertEqual(task_ai_describer.classify_task_for_aa360(integration_task), "integracion")

        utility_task = dict(self.task)
        utility_task.update(
            {
                "name": "FormatDate",
                "role": "subtask",
                "is_entrypoint": False,
                "actions": ["Formatear fecha"],
                "comments": ["Helper reutilizable"],
                "systems": [],
                "task_calls": [],
            }
        )
        self.assertEqual(task_ai_describer.classify_task_for_aa360(utility_task), "utilitario")


if __name__ == "__main__":
    unittest.main()
