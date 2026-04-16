import json
import os
import unittest
from unittest.mock import patch
from urllib import error

from app.analysis import flow_builder, task_ai_describer


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FlowAndAIEdgeCoverageTests(unittest.TestCase):
    def test_build_flow_handles_empty_tasks(self):
        result = flow_builder.build_flow([])
        self.assertEqual(result["summary"]["total_nodes"], 0)
        self.assertEqual(result["summary"]["total_edges"], 0)

    def test_build_flow_deduplicates_and_ignores_unknown_targets(self):
        tasks = [
            {
                "name": "Main",
                "path": "A/Main",
                "is_entrypoint": True,
                "dependencies": [
                    {"path": "A/Sub", "type": "runTask"},
                    {"path": "A/Sub", "type": "runTask"},
                    {"path": "A/Missing", "type": "runTask"},
                ],
                "task_calls": [
                    {
                        "target_path": "A/Sub",
                        "inputs": [{"name": "In"}],
                        "outputs": [{"name": "Out"}],
                    }
                ],
                "node_stats": {"total_nodes": 3},
            },
            {
                "name": "Sub",
                "path": "A/Sub",
                "dependencies": [],
                "task_calls": [],
                "node_stats": {"total_nodes": 1},
            },
        ]

        result = flow_builder.build_flow(tasks)
        self.assertEqual(result["summary"]["total_edges"], 1)
        self.assertEqual(result["edges"][0]["inputs_count"], 1)
        self.assertEqual(result["edges"][0]["outputs_count"], 1)

    def test_build_flow_cycle_falls_back_to_original_order(self):
        tasks = [
            {
                "name": "A",
                "path": "A",
                "dependencies": [{"path": "B", "type": "runTask"}],
                "task_calls": [],
                "node_stats": {"total_nodes": 1},
            },
            {
                "name": "B",
                "path": "B",
                "dependencies": [{"path": "A", "type": "runTask"}],
                "task_calls": [],
                "node_stats": {"total_nodes": 1},
            },
        ]
        result = flow_builder.build_flow(tasks)
        self.assertEqual([node["name"] for node in result["nodes"]], ["A", "B"])

    def test_extract_model_json_and_normalizers(self):
        self.assertEqual(task_ai_describer._extract_model_json("```json\n{\"x\":1}\n```"), {"x": 1})
        self.assertEqual(task_ai_describer._extract_model_json("prefix {\"k\":2} suffix"), {"k": 2})
        self.assertIsNone(task_ai_describer._extract_model_json("not json"))

        self.assertEqual(task_ai_describer._normalize_level("ALTA"), "alta")
        self.assertEqual(task_ai_describer._normalize_level("x"), "media")
        self.assertEqual(task_ai_describer._normalize_task_profile("Integracion"), "integracion")
        self.assertEqual(task_ai_describer._normalize_task_profile("x"), "utilitario")
        self.assertEqual(task_ai_describer._normalize_severity("BLOQUEANTE"), "bloqueante")
        self.assertEqual(task_ai_describer._normalize_severity("x"), "medio")
        self.assertEqual(task_ai_describer._normalize_effort("l"), "L")
        self.assertEqual(task_ai_describer._normalize_effort("x"), "M")
        self.assertEqual(task_ai_describer._normalize_priority("p1"), "P1")
        self.assertEqual(task_ai_describer._normalize_priority("x"), "P2")

        self.assertEqual(task_ai_describer._normalize_list("uno", "def"), ["uno"])
        self.assertEqual(task_ai_describer._normalize_list([], "def"), ["def"])

    def test_normalize_priority_findings_and_sprint_plan(self):
        findings = task_ai_describer._normalize_priority_findings(
            [
                "x",
                {"severity": "alto", "title": "T", "why": "W", "task": "Main"},
                {"severity": "bad"},
            ]
        )
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["severity"], "alto")
        self.assertEqual(findings[1]["severity"], "medio")

        plan = task_ai_describer._normalize_sprint_plan(
            [
                "x",
                {
                    "priority": "p1",
                    "action": "A",
                    "effort": "s",
                    "impact": "I",
                    "owner": "dev",
                    "tasks": "Main",
                    "done_criteria": "Ready",
                },
                {
                    "priority": "x",
                    "tasks": 1,
                    "done_criteria": 2,
                },
            ]
        )
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0]["priority"], "P1")
        self.assertEqual(plan[0]["tasks"], ["Main"])
        self.assertEqual(plan[0]["done_criteria"], ["Ready"])
        self.assertEqual(plan[1]["priority"], "P2")
        self.assertTrue(plan[1]["done_criteria"])

    def test_describe_task_with_ai_fallbacks_on_provider_issues(self):
        task = {
            "name": "Main",
            "role": "main",
            "actions": ["Validar"],
            "comments": [],
            "dependencies": [],
            "task_calls": [],
            "systems": [],
            "packages": [],
            "triggers": [],
            "credentials": [],
            "variables": {"input": [], "output": [], "internal": []},
            "node_stats": {"total_nodes": 1},
            "error_handling": {"has_try": False, "has_catch": False, "has_finally": False},
            "type": "taskbot",
            "is_entrypoint": True,
        }

        with patch.dict(os.environ, {"AI_QUALITY_ENABLED": "true"}, clear=True):
            result = task_ai_describer.describe_task_with_ai(task)
            self.assertEqual(result["source"], "heuristic")

        with patch.dict(
            os.environ,
            {"AI_QUALITY_ENABLED": "true", "OPENAI_API_KEY": "k", "OPENAI_BASE_URL": "https://x/v1"},
            clear=True,
        ), patch(
            "app.analysis.task_ai_describer.request.urlopen",
            side_effect=error.URLError("down"),
        ):
            result = task_ai_describer.describe_task_with_ai(task)
            self.assertEqual(result["source"], "heuristic")

        bad_payload = {"choices": [{"message": {"content": "not-json"}}]}
        with patch.dict(
            os.environ,
            {"AI_QUALITY_ENABLED": "true", "OPENAI_API_KEY": "k", "OPENAI_BASE_URL": "https://x/v1"},
            clear=True,
        ), patch(
            "app.analysis.task_ai_describer.request.urlopen",
            return_value=_FakeResponse(json.dumps(bad_payload).encode("utf-8")),
        ):
            result = task_ai_describer.describe_task_with_ai(task)
            self.assertEqual(result["source"], "heuristic")

    def test_build_sdd_and_prioritization_ai_paths(self):
        project_data = {
            "name": "DemoBot",
            "metadata": {"description": "Desc", "entrypoints": ["Main"]},
            "tasks": [
                {
                    "name": "Main",
                    "role": "main",
                    "type": "taskbot",
                    "is_entrypoint": True,
                    "actions": ["Run"],
                    "task_calls": [{"target_name": "Sub"}],
                    "dependencies": [{"name": "Sub"}],
                    "systems": [{"type": "url", "value": "https://x"}],
                    "packages": [{"name": "Browser", "version": "1"}],
                    "triggers": [{"type": "manual"}],
                    "credentials": [{"credential_name": "AA360_LOGIN"}],
                    "error_handling": {"has_try": True, "has_catch": False},
                    "node_stats": {"total_nodes": 2},
                }
            ],
            "systems": [{"type": "url", "value": "https://x"}],
            "packages": [{"name": "Browser", "version": "1"}],
            "credentials": [],
        }

        sdd_payload = {
            "choices": [
                {
                    "message": {
                        "content": "```json\n{\"executive_summary\":[\"a\"],\"critical_points\":[\"b\"],\"confidence\":\"alta\"}\n```"
                    }
                }
            ]
        }
        pri_payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "priority_findings": [{"severity": "alto", "title": "T", "why": "W", "task": "Main"}],
                                "sprint_plan": [
                                    {
                                        "priority": "P1",
                                        "action": "Fix",
                                        "effort": "S",
                                        "impact": "High",
                                        "owner": "dev",
                                        "tasks": ["Main"],
                                        "done_criteria": ["ok"],
                                    }
                                ],
                                "confidence": "alta",
                            }
                        )
                    }
                }
            ]
        }

        with patch.dict(
            os.environ,
            {"AI_QUALITY_ENABLED": "true", "OPENAI_API_KEY": "k", "OPENAI_BASE_URL": "https://x/v1"},
            clear=True,
        ), patch("app.analysis.task_ai_describer.request.urlopen", return_value=_FakeResponse(json.dumps(sdd_payload).encode("utf-8"))):
            sdd = task_ai_describer.build_sdd_ai_insights(project_data, {"summary": {"total_edges": 1}})
            self.assertEqual(sdd["source"], "ai")
            self.assertEqual(sdd["confidence"], "alta")

        with patch.dict(
            os.environ,
            {"AI_QUALITY_ENABLED": "true", "OPENAI_API_KEY": "k", "OPENAI_BASE_URL": "https://x/v1"},
            clear=True,
        ), patch("app.analysis.task_ai_describer.request.urlopen", return_value=_FakeResponse(json.dumps(pri_payload).encode("utf-8"))):
            pri = task_ai_describer.build_quality_prioritization(
                project_data,
                {"Main": {"task_profile": "principal", "criticality": "alta", "risks": ["r"], "recommendations": ["m"]}},
                ["obs"],
            )
            self.assertEqual(pri["source"], "ai")
            self.assertEqual(pri["confidence"], "alta")
            self.assertEqual(pri["priority_findings"][0]["severity"], "alto")

    def test_heuristic_helpers_misc(self):
        self.assertEqual(task_ai_describer._safe_timeout("-1"), 25)
        self.assertEqual(task_ai_describer._safe_timeout("x"), 25)
        self.assertEqual(task_ai_describer._safe_timeout("12"), 12)

        findings = [
            {"severity": "bajo", "task": "A"},
            {"severity": "bloqueante", "task": "Main"},
            {"severity": "alto", "task": "Main"},
        ]
        sorted_findings = task_ai_describer._sort_findings_by_severity(findings)
        self.assertEqual(sorted_findings[0]["severity"], "bloqueante")
        self.assertEqual(task_ai_describer._extract_task_name_from_observation("**Main** fallo"), "Main")
        self.assertEqual(task_ai_describer._extract_task_name_from_observation("sin formato"), "General")
        self.assertEqual(task_ai_describer._top_tasks_from_findings(findings, limit=2), ["A", "Main"])

        heur = task_ai_describer._heuristic_sdd_insights(
            {
                "name": "Demo",
                "metadata": {"entrypoints": []},
                "tasks": [{"name": "Main", "type": "taskbot", "error_handling": {"has_try": True}, "task_calls": [], "node_stats": {"disabled_nodes": 0}}],
                "systems": [],
            },
            {"summary": {"total_edges": 0}},
        )
        self.assertEqual(heur["source"], "heuristic")
        self.assertTrue(heur["critical_points"])


if __name__ == "__main__":
    unittest.main()
