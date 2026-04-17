import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from app.parser import project_parser
from app.parser import _documents as documents_parser
from app.parser import _node_analysis
from app.parser import _project_support


class ParserAdditionalCoverageTests(unittest.TestCase):
    def test_manifest_and_discovery_fallback_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "Project"
            root.mkdir(parents=True, exist_ok=True)

            # Invalid manifest should be tolerated
            (root / "manifest.json").write_text("{bad-json", encoding="utf-8")
            manifest = project_parser._load_manifest(root)
            self.assertEqual(manifest, {})

            # Fallback discovery by taskbot shape
            bot_file = root / "Automation Anywhere" / "Bots" / "Demo" / "Main"
            bot_file.parent.mkdir(parents=True, exist_ok=True)
            bot_file.write_text(
                json.dumps({"nodes": [], "variables": [], "packages": [], "properties": {}}),
                encoding="utf-8",
            )

            entries = project_parser._discover_task_entries(root, {})
            self.assertTrue(any(entry.get("contentType") == project_parser.TASKBOT_CONTENT_TYPE for entry in entries))

    def test_parse_entry_and_role_helpers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "Project"
            root.mkdir(parents=True, exist_ok=True)

            xml_path = root / "doc.xml"
            xml_path.write_text("<root Description='Desc'><action Name='Paso'/></root>", encoding="utf-8")
            json_path = root / "doc.json"
            json_path.write_text(json.dumps({"description": "Desc", "inputVars": {"A": 1}}), encoding="utf-8")
            txt_path = root / "doc.txt"
            txt_path.write_text("x", encoding="utf-8")

            with self.assertRaises(json.JSONDecodeError):
                project_parser._parse_task_entry(root, {"path": "doc.xml"})
            self.assertEqual(project_parser._parse_task_entry(root, {"path": "doc.json"})["type"], "json")
            with self.assertRaises(json.JSONDecodeError):
                project_parser._parse_task_entry(root, {"path": "doc.txt"})
            self.assertIsNone(project_parser._parse_task_entry(root, {"path": "missing.json"}))

            self.assertEqual(project_parser._detect_role("A\\Tareas\\X", "Task"), "subtask")
            self.assertEqual(project_parser._detect_role("A\\B", "Main"), "main")
            self.assertEqual(project_parser._detect_role("A\\B", "Task"), "taskbot")

    def test_summarize_extract_and_sanitize_helpers(self):
        self.assertEqual(project_parser._summarize_node({"commandName": "try", "packageName": "ErrorHandler"}, 1), "Inicio de bloque de manejo de errores")
        self.assertEqual(project_parser._summarize_node({"commandName": "catch", "packageName": "ErrorHandler"}, 1), "Captura y trata errores")
        self.assertEqual(project_parser._summarize_node({"commandName": "finally", "packageName": "ErrorHandler"}, 1), "Ejecuta acciones de cierre")
        self.assertIn("base de datos", project_parser._summarize_node({"commandName": "connect", "packageName": "Database"}, 1))
        self.assertIn("navegador", project_parser._summarize_node({"commandName": "openBrowser", "packageName": "Browser"}, 1))
        self.assertIsNone(project_parser._summarize_node({"commandName": "noop", "packageName": "x"}, 2))

        call = project_parser._extract_task_call(
            {
                "commandName": "runTask",
                "attributes": [
                    {
                        "name": "taskbot",
                        "value": {
                            "taskbotFile": {"string": "repository:///Automation%20Anywhere/Bots/Demo/Sub"},
                            "taskbotInput": {"dictionary": [{"key": "InA", "value": {"string": "$A$"}}]},
                        },
                    }
                ],
                "returnTo": {"dictionary": [{"key": "OutA", "value": {"variableName": "vA"}}]},
            }
        )
        self.assertEqual(call["target_name"], "Sub")
        self.assertEqual(call["inputs"][0]["name"], "InA")
        self.assertEqual(call["outputs"][0]["name"], "OutA")

        flattened = project_parser._flatten_attribute_values(
            {
                "string": "abc",
                "inner": {"expression": "${x}", "blob": "IGNORED", "n": 5},
                "arr": [{"string": "k"}, "v"],
            }
        )
        self.assertIn("abc", flattened)
        self.assertIn("${x}", flattened)
        self.assertIn("5", flattened)
        self.assertIn("k", flattened)
        self.assertIn("v", flattened)

        # system extractor skips ui noise and captures db/url/file
        systems = project_parser._extract_systems_from_node(
            {
                "commandName": "connect",
                "packageName": "Database",
                "attributes": [
                    {"name": "windowTitle", "value": {"string": "ignore"}},
                    {"name": "jdbc", "value": {"string": "jdbc:mysql://db.local?user=a&password=b"}},
                    {"name": "url", "value": {"string": "https://example.com"}},
                    {"name": "path", "value": {"string": r"C:\\Users\\sebas\\file.txt"}},
                ],
            }
        )
        types = {item["type"] for item in systems}
        self.assertTrue({"database", "url", "file"}.issubset(types))

        # credential extractor and sanitize fallbacks
        credential = project_parser._extract_credential_from_node(
            {
                "commandName": "get",
                "packageName": "CredentialVault",
                "attributes": [
                    {"name": "credentialName", "value": {"string": "RPA_DB"}},
                    {"name": "attributeName", "value": {"string": "pwd"}},
                    {"name": "lockerName", "value": {"string": "Default"}},
                ],
            }
        )
        self.assertEqual(credential["credential_name"], "RPA_DB")
        self.assertEqual(project_parser.sanitize_text(True), "true")
        self.assertEqual(project_parser._normalize_repository_path("repository:///A%20B/C"), f"A B{project_parser.os.sep}C")

    def test_xml_json_parsers_error_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bad_xml = root / "bad.xml"
            bad_json = root / "bad.json"
            bad_xml.write_text("<root>", encoding="utf-8")
            bad_json.write_text("{", encoding="utf-8")

            self.assertIsNone(project_parser._parse_xml_file(str(bad_xml), "bad.xml"))
            self.assertIsNone(project_parser._parse_json_file(str(bad_json), "bad.json"))

    def test_xml_json_action_extractors_exception_branches(self):
        class _BrokenRoot:
            def iter(self):
                raise RuntimeError("boom")

        self.assertEqual(project_parser._extract_variables_from_xml(_BrokenRoot()), {"input": [], "output": []})
        self.assertEqual(project_parser._extract_actions_from_xml(_BrokenRoot()), [])

        class _BrokenDict(dict):
            def items(self):
                raise RuntimeError("boom")

        self.assertEqual(project_parser._extract_variables_from_json(_BrokenDict()), {"input": [], "output": []})

    def test_parse_taskbot_and_misc_helpers(self):
        data = {
            "nodes": [
                {"commandName": "Comment", "packageName": "Comment", "attributes": [{"name": "comment", "value": {"string": "Developer: Bob"}}]},
                {"commandName": "Comment", "packageName": "Comment", "attributes": [{"name": "comment", "value": {"string": "Descripcion: Demo"}}]},
            ],
            "variables": [
                {"name": "GblA", "type": "STRING", "input": False, "output": False, "description": "x", "defaultValue": {"string": "d"}},
                {"name": "InB", "type": "NUMBER", "input": True, "output": False, "description": "", "defaultValue": {"number": 1}},
                {"name": "OutC", "type": "BOOLEAN", "input": False, "output": True, "description": "", "defaultValue": {"boolean": True}},
            ],
            "packages": [{"name": "Browser", "version": "1.0"}, "ignore"],
            "properties": {"password": "secret", "x": ["a", {"token": "abc"}]},
            "triggers": [{"type": "manual"}, "x"],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            task_path = root / "Main"
            task_path.write_text(json.dumps(data), encoding="utf-8")

            parsed = project_parser._parse_taskbot(task_path, root, data, {"manualDependencies": [], "scannedDependencies": []})
            self.assertEqual(parsed["name"], "Main")
            self.assertEqual(parsed["developer"], "Bob")
            self.assertEqual(parsed["description"], "Demo")
            self.assertEqual(parsed["variables"]["internal"][0]["scope"], "global")
            self.assertEqual(parsed["variables"]["input"][0]["scope"], "input")
            self.assertEqual(parsed["variables"]["output"][0]["scope"], "output")

        # _parse_xml_file returns a minimal structure even when extraction helpers fail
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_path = Path(temp_dir) / "doc.xml"
            xml_path.write_text("<root><step Name='S1'/></root>", encoding="utf-8")
            with patch("app.parser.project_parser._extract_variables_from_xml", side_effect=RuntimeError("x")):
                doc = project_parser._parse_xml_file(str(xml_path), "doc.xml")
                self.assertIsNone(doc)

    def test_project_parser_facade_and_error_branches(self):
        with self.assertRaises(FileNotFoundError):
            project_parser.parse_project(Path("C:/this/path/does/not/exist/aa360"))

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch("app.parser.project_parser._load_manifest", return_value={}):
                with patch(
                    "app.parser.project_parser._discover_task_entries",
                    return_value=[{"path": "a"}, {"path": "b"}],
                ):
                    with patch(
                        "app.parser.project_parser._parse_task_entry",
                        side_effect=[
                            RuntimeError("boom"),
                            {
                                "name": "B",
                                "path": "b",
                                "is_entrypoint": False,
                                "role": "taskbot",
                                "description": "",
                                "dependencies": [],
                                "packages": [],
                                "systems": [],
                                "credentials": [],
                            },
                        ],
                    ):
                        result = project_parser.parse_project(root)
                        self.assertEqual(result["task_count"], 1)

            no_dict = root / "node.txt"
            no_dict.write_text("{}", encoding="utf-8")
            with patch("app.parser.project_parser._load_json", return_value=["not-dict"]):
                self.assertIsNone(project_parser._parse_task_entry(root, {"path": "node.txt"}))

        self.assertEqual(project_parser._infer_variable_scope("GblName"), "global")
        self.assertEqual(project_parser._infer_variable_scope("LocName"), "local")
        self.assertEqual(project_parser._infer_variable_scope("InName"), "input")
        self.assertEqual(project_parser._infer_variable_scope("OutName"), "output")
        self.assertEqual(project_parser._infer_variable_scope("Other"), "unspecified")

        self.assertIsInstance(project_parser._sanitize_packages([{"name": "A", "version": "1"}]), list)
        self.assertIsInstance(project_parser._sanitize_triggers([{"type": "manual"}]), list)
        self.assertEqual(project_parser._sanitize_mapping({"token": "abc"})["token"], "<redacted>")

        node = {
            "commandName": "Comment",
            "attributes": [
                {"name": "comment", "value": {"string": "Descripcion: prueba"}},
                {"name": "title", "value": {"string": "Titulo"}},
            ]
        }
        self.assertIn("prueba", project_parser._extract_comment_text(node))
        self.assertTrue(project_parser._is_header_comment("Descripcion: test"))
        self.assertIsNotNone(project_parser._get_attribute(node, "title"))
        self.assertEqual(project_parser._get_attribute_string(node, "title"), "Titulo")
        self.assertEqual(project_parser._extract_value_literal({"number": 7}), 7)

        xml_root = ET.fromstring("<root><step Name='S1' /></root>")
        self.assertEqual(project_parser._extract_variables_from_xml(xml_root), {"input": [], "output": []})
        self.assertEqual(project_parser._extract_variables_from_json({"outputVars": {"A": 1}})["output"][0]["name"], "A")
        self.assertEqual(project_parser._extract_actions_from_xml(xml_root), ["S1"])

        self.assertEqual(project_parser._should_skip_file(Path("a/metadata/file.json")), True)
        self.assertEqual(project_parser._looks_like_taskbot(Path("a/taskbot.json")), False)

    def test_node_analysis_uncovered_branches(self):
        metadata = _node_analysis.extract_header_metadata(
            [
                {"commandName": "Comment", "attributes": []},
                {
                    "commandName": "Comment",
                    "attributes": [{"name": "comment", "value": {"string": "sin separador"}}],
                },
            ]
        )
        self.assertEqual(metadata, {})

        variables = _node_analysis.extract_taskbot_variables(
            ["invalid", {"name": "InA", "type": "STRING", "input": True, "output": False}],
            infer_variable_scope=lambda _name: "input",
        )
        self.assertEqual(len(variables["input"]), 1)

        analysis = {
            "actions": [],
            "task_calls": [],
            "systems": [],
            "credentials": [],
            "comments": [],
            "stats": {
                "total_nodes": 0,
                "disabled_nodes": 0,
                "decision_nodes": 0,
                "loop_nodes": 0,
                "task_calls": 0,
                "error_handlers": 0,
                "step_groups": 0,
            },
            "error_handling": {"has_try": False, "has_catch": False, "has_finally": False},
        }
        _node_analysis.visit_node(
            "not-a-dict",
            analysis,
            set(),
            0,
            extract_task_call=lambda _n: None,
            summarize_node=lambda _n, _d: None,
            should_keep_summary=lambda _n, _d: True,
        )

        self.assertEqual(_node_analysis.summarize_node({"commandName": "step", "packageName": "Step"}, 1, lambda _n: None), "Grupo de pasos")
        self.assertEqual(_node_analysis.summarize_node({"commandName": "runTask", "packageName": "TaskBot"}, 1, lambda _n: None), "Invoca una subtask")
        self.assertIn(
            "Consulta registros",
            _node_analysis.summarize_node({"commandName": "exportToDataTable", "packageName": "Database"}, 1, lambda _n: None),
        )
        self.assertIn(
            "Actualiza informacion",
            _node_analysis.summarize_node({"commandName": "insertUpdateDelete", "packageName": "Database"}, 1, lambda _n: None),
        )
        self.assertIn(
            "Cierra conexion",
            _node_analysis.summarize_node({"commandName": "disconnect", "packageName": "Database"}, 1, lambda _n: None),
        )
        self.assertIn(
            "Cierra el navegador",
            _node_analysis.summarize_node({"commandName": "close", "packageName": "Browser"}, 1, lambda _n: None),
        )
        self.assertIn(
            "Registra trazas",
            _node_analysis.summarize_node({"commandName": "any", "packageName": "LogToFile"}, 1, lambda _n: None),
        )
        self.assertIn(
            "Interactua",
            _node_analysis.summarize_node({"commandName": "any", "packageName": "Recorder"}, 1, lambda _n: None),
        )
        self.assertIn(
            "Captura evidencia",
            _node_analysis.summarize_node({"commandName": "captureWindow", "packageName": "Screen"}, 1, lambda _n: None),
        )

        self.assertIsNone(_node_analysis.extract_task_call({"attributes": []}))

        no_credential = _node_analysis.extract_credential_from_node(
            {
                "commandName": "get",
                "packageName": "CredentialVault",
                "attributes": ["invalid", {"name": "lockerName", "value": {"string": "Default"}}],
            }
        )
        self.assertIsNone(no_credential)

        systems = _node_analysis.extract_systems_from_node(
            {
                "commandName": "open",
                "packageName": "Browser",
                "attributes": [
                    "invalid",
                    {"name": "path", "value": {"string": ""}},
                    {"name": "url", "value": {"string": "https://example.com"}},
                ],
            }
        )
        self.assertTrue(any(item["type"] == "url" for item in systems))

        sql_systems = _node_analysis.extract_systems_from_node(
            {"commandName": "exportToDataTable", "packageName": "Database", "attributes": []}
        )
        self.assertTrue(any(item["value"] == "Operacion SQL" for item in sql_systems))

    def test_documents_uncovered_branches(self):
        logger = type("Logger", (), {"debug": lambda *_args, **_kwargs: None})()
        xml_root = ET.fromstring("<root><output Name='OutA' Type='String' Value='ok'/><task Name='DoX'/></root>")

        xml_vars = documents_parser.extract_variables_from_xml(xml_root, logger)
        self.assertEqual(xml_vars["output"][0]["name"], "OutA")
        self.assertEqual(documents_parser.extract_actions_from_xml(xml_root, logger), ["DoX"])

        self.assertEqual(documents_parser.extract_variables_from_json([1, 2, 3], logger), {"input": [], "output": []})
        out_vars = documents_parser.extract_variables_from_json({"outputVars": {"OutB": 1}}, logger)
        self.assertEqual(out_vars["output"][0]["name"], "OutB")

    def test_project_parser_last_misses_and_common_helpers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            xml_entry = root / "doc.xml"
            xml_entry.write_text("<root><input Name='I'/></root>", encoding="utf-8")
            with patch("app.parser.project_parser._load_json", return_value={}):
                xml_result = project_parser._parse_task_entry(root, {"path": "doc.xml"})
            self.assertEqual(xml_result["type"], "xml")

            unknown_entry = root / "doc.dat"
            unknown_entry.write_text("payload", encoding="utf-8")
            with patch("app.parser.project_parser._load_json", return_value={}):
                self.assertIsNone(project_parser._parse_task_entry(root, {"path": "doc.dat"}))

        analysis = {
            "actions": [],
            "task_calls": [],
            "systems": [],
            "credentials": [],
            "comments": [],
            "stats": {
                "total_nodes": 0,
                "disabled_nodes": 0,
                "decision_nodes": 0,
                "loop_nodes": 0,
                "task_calls": 0,
                "error_handlers": 0,
                "step_groups": 0,
            },
            "error_handling": {"has_try": False, "has_catch": False, "has_finally": False},
        }
        project_parser._visit_node(
            {"commandName": "step", "packageName": "Step", "attributes": []},
            analysis,
            set(),
            0,
        )
        self.assertGreaterEqual(analysis["stats"]["total_nodes"], 1)

        self.assertEqual(project_parser.sanitize_text(None), "")
        self.assertEqual(project_parser._normalize_repository_path(""), "")
        self.assertEqual(
            project_parser._extract_value_literal({"taskbotFile": {"expression": "repository:///A/B"}}),
            "repository:///A/B",
        )
        self.assertEqual(
            project_parser._extract_value_literal({"dictionary": [{"key": "K1"}, {"key": "K2"}, "x"]}),
            "K1, K2",
        )
        self.assertEqual(project_parser._extract_value_literal(5), 5)
        self.assertEqual(project_parser._flatten_attribute_values(None), [])
        self.assertEqual(project_parser._sanitize_mapping("x"), {})
        self.assertEqual(project_parser._sanitize_mapping({"outer": {"inner": "ok"}})["outer"]["inner"], "ok")

    def test_project_support_remaining_branches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            # A valid file for manifest path checks
            bot = root / "Automation Anywhere" / "Bots" / "Main"
            bot.parent.mkdir(parents=True, exist_ok=True)
            bot.write_text("{}", encoding="utf-8")

            manifest = {
                "files": [
                    # ignored by contentType mismatch
                    {"contentType": "text/plain", "path": str(bot.relative_to(root))},
                    # ignored by missing path
                    {"contentType": project_parser.TASKBOT_CONTENT_TYPE, "path": ""},
                    # accepted
                    {"contentType": project_parser.TASKBOT_CONTENT_TYPE, "path": str(bot.relative_to(root))},
                ]
            }
            entries = _project_support.discover_task_entries(root, manifest)
            self.assertEqual(len(entries), 1)

            # mark_entrypoints early return path
            self.assertEqual(_project_support.mark_entrypoints([]), [])

            # build_file_summary: force other_count branch
            misc = root / "notes.txt"
            misc.write_text("hello", encoding="utf-8")
            summary = _project_support.build_file_summary(root, manifest={}, tasks=[])
            self.assertEqual(summary["other_count"], 2)


if __name__ == "__main__":
    unittest.main()
