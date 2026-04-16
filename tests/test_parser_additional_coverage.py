import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.parser import project_parser


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


if __name__ == "__main__":
    unittest.main()
