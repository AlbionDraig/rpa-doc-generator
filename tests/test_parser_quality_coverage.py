import json
import tempfile
import unittest
from pathlib import Path

from app.generator import sdd_generator
from app.parser import project_parser


class ParserAndQualityCoverageTests(unittest.TestCase):
    """
    Tests unitarios dirigidos a mejorar la cobertura del parser y el generador.

    Cubren helpers internos de project_parser (sanitización, análisis de nodos,
    detección de dependencias y entrypoints, recopilación de sistemas y
    credenciales, parseo sin manifest) y funciones de sdd_generator
    (observaciones de calidad, generación y escritura del SDD).
    """

    def test_sanitize_text_masks_sensitive_data(self):
        """
        sanitize_text redacta credenciales, rutas de usuario y URLs sensibles.

        Casos cubiertos:
        - campo con nombre sensible (password) → '<redacted>'
        - URL con query param 'password' → '<redacted>' (regex SENSITIVE)
        - ruta Windows con nombre de usuario → usuario reemplazado por '<user>'
        - cadena de conexión JDBC con user/password → params redactados
        - ruta file:// con usuario Windows → usuario redactado
        """
        self.assertEqual(project_parser.sanitize_text("abc", field_name="password"), "<redacted>")
        self.assertEqual(
            project_parser.sanitize_text("https://api.local?a=1&password=secret"),
            "<redacted>",
        )
        self.assertEqual(
            project_parser.sanitize_text(r"C:\Users\sebas\Desktop\bot"),
            r"C:\Users\<user>\Desktop\bot",
        )
        self.assertEqual(
            project_parser.sanitize_text("jdbc:mysql://db.local:3306/app?user=admin&password=secret"),
            "jdbc:mysql://db.local:3306/app?user=<redacted>&password=<redacted>",
        )
        self.assertEqual(
            project_parser.sanitize_text(r"file://C:\Users\sebas\Downloads\run.txt"),
            r"file://C:\Users\<user>\Downloads\run.txt",
        )

    def test_analyze_nodes_extracts_stats_calls_systems_and_credentials(self):
        """
        _analyze_nodes clasifica correctamente un árbol de nodos AA360.

        El árbol incluye: comentario de cabecera (ignorado), comentario
        funcional (capturado), Step, If deshabilitado, Loop, bloque
        try/catch/finally, runTask con contrato de variables, nodo Browser
        con URL y ruta de archivo, nodo Database con JDBC y nodo
        CredentialVault. Verifica contadores, flags de error handling,
        extracción de comentarios, task_calls, sistemas y credenciales.
        """
        nodes = [
            {
                "commandName": "Comment",
                "packageName": "Comment",
                "attributes": [{"name": "comment", "value": {"string": "Developer: Alice"}}],
            },
            {
                "commandName": "Comment",
                "packageName": "Comment",
                "attributes": [{"name": "comment", "value": {"string": "Procesa clientes"}}],
            },
            {
                "commandName": "Step",
                "packageName": "Step",
                "attributes": [{"name": "title", "value": {"string": "Carga"}}],
            },
            {
                "commandName": "if",
                "packageName": "If",
                "disabled": True,
                "attributes": [],
            },
            {
                "commandName": "loopEach",
                "packageName": "Loop",
                "attributes": [],
            },
            {
                "commandName": "try",
                "packageName": "ErrorHandler",
                "attributes": [],
                "children": [{"commandName": "catch", "packageName": "ErrorHandler", "attributes": []}],
                "branches": [{"commandName": "finally", "packageName": "ErrorHandler", "attributes": []}],
            },
            {
                "commandName": "runTask",
                "packageName": "TaskBot",
                "attributes": [
                    {
                        "name": "taskbot",
                        "value": {
                            "taskbotFile": {
                                "string": "repository:///Automation%20Anywhere/Bots/Demo/Subtasks/Lookup"
                            },
                            "taskbotInput": {
                                "dictionary": [
                                    {"key": "InCustomer", "value": {"string": "$LocCustomer$"}}
                                ]
                            },
                        },
                    }
                ],
                "returnTo": {
                    "dictionary": [
                        {"key": "OutStatus", "value": {"variableName": "LocStatus"}},
                    ]
                },
            },
            {
                "commandName": "openBrowser",
                "packageName": "Browser",
                "attributes": [
                    {"name": "url", "value": {"string": "https://example.com/login"}},
                    {"name": "path", "value": {"string": r"C:\\Users\\sebas\\tmp\\screen.png"}},
                ],
            },
            {
                "commandName": "connect",
                "packageName": "Database",
                "attributes": [
                    {
                        "name": "connectionString",
                        "value": {"string": "jdbc:mysql://db.local:3306/app?user=admin&password=secret"},
                    }
                ],
            },
            {
                "commandName": "get",
                "packageName": "CredentialVault",
                "attributes": [
                    {"name": "credentialName", "value": {"string": "RPA_DB"}},
                    {"name": "attributeName", "value": {"string": "password"}},
                    {"name": "lockerName", "value": {"string": "Default"}},
                ],
            },
        ]

        analysis = project_parser._analyze_nodes(nodes)

        self.assertGreaterEqual(analysis["stats"]["total_nodes"], 12)
        self.assertEqual(analysis["stats"]["disabled_nodes"], 1)
        self.assertEqual(analysis["stats"]["decision_nodes"], 1)
        self.assertEqual(analysis["stats"]["loop_nodes"], 1)
        self.assertEqual(analysis["stats"]["task_calls"], 1)
        self.assertTrue(analysis["error_handling"]["has_try"])
        self.assertTrue(analysis["error_handling"]["has_catch"])
        self.assertTrue(analysis["error_handling"]["has_finally"])

        self.assertIn("Procesa clientes", analysis["comments"])
        self.assertTrue(any(call["target_name"] == "Lookup" for call in analysis["task_calls"]))
        self.assertTrue(any(item["type"] == "url" for item in analysis["systems"]))
        self.assertTrue(any(item["type"] == "database" for item in analysis["systems"]))
        self.assertTrue(any(item["type"] == "file" for item in analysis["systems"]))
        self.assertEqual(analysis["credentials"][0]["credential_name"], "RPA_DB")

    def test_dependency_entrypoints_and_collections(self):
        """
        _merge_dependencies, _mark_entrypoints y funciones de recopilación.

        Verifica que:
        - _merge_dependencies deduplica y preserva tipos (runTask, manual).
        - _mark_entrypoints marca correctamente Main como entrypoint y A como no.
        - _collect_project_packages combina y ordena paquetes sin duplicados.
        - _collect_project_systems deduplica por (tipo, valor).
        - _collect_project_credentials deduplica por (nombre, atributo).
        - _select_project_description devuelve la primera descripción no vacía.
        """
        task_calls = [
            {"target_path": "Automation Anywhere/Bots/Demo/Subtasks/A"},
            {"target_path": "Automation Anywhere/Bots/Demo/Subtasks/A"},
        ]
        manifest_entry = {
            "manualDependencies": ["Automation Anywhere/Bots/Demo/Subtasks/B"],
            "scannedDependencies": ["Automation Anywhere/Bots/Demo/Subtasks/A"],
        }
        dependencies = project_parser._merge_dependencies(manifest_entry, task_calls)
        self.assertEqual(len(dependencies), 2)
        self.assertEqual(dependencies[0]["type"], "runTask")
        self.assertEqual(dependencies[1]["type"], "manual")

        tasks = [
            {
                "name": "Main",
                "path": project_parser._normalize_path_text("Automation Anywhere/Bots/Main"),
                "role": "main",
                "dependencies": [
                    {
                        "path": project_parser._normalize_path_text("Automation Anywhere/Bots/Subtasks/A"),
                        "type": "runTask",
                    }
                ],
                "packages": [{"name": "TaskBot", "version": "1.0"}],
                "systems": [{"type": "url", "value": "https://example.com", "source": "browser::open"}],
                "credentials": [
                    {"credential_name": "RPA_DB", "attribute": "password", "vault": "Default"}
                ],
                "description": "",
            },
            {
                "name": "A",
                "path": project_parser._normalize_path_text("Automation Anywhere/Bots/Subtasks/A"),
                "role": "subtask",
                "dependencies": [],
                "packages": [{"name": "String", "version": "2.0"}],
                "systems": [{"type": "url", "value": "https://example.com", "source": "browser::open"}],
                "credentials": [
                    {"credential_name": "RPA_DB", "attribute": "password", "vault": "Default"}
                ],
                "description": "Descripcion A",
            },
        ]

        marked = project_parser._mark_entrypoints(tasks)
        self.assertTrue(marked[0]["is_entrypoint"])
        self.assertFalse(marked[1]["is_entrypoint"])

        packages = project_parser._collect_project_packages(
            {"packages": [{"name": "TaskBot", "version": "1.0"}]},
            marked,
        )
        self.assertEqual([pkg["name"] for pkg in packages], ["String", "TaskBot"])

        systems = project_parser._collect_project_systems(marked)
        self.assertEqual(len(systems), 1)
        credentials = project_parser._collect_project_credentials(marked)
        self.assertEqual(len(credentials), 1)
        self.assertEqual(project_parser._select_project_description(marked), "Descripcion A")

    def test_parse_project_and_file_summary_without_manifest(self):
        """
        parse_project detecta taskbots por estructura JSON cuando no hay manifest.

        Construye un proyecto mínimo sin manifest.json que contiene:
        - un taskbot JSON válido (con nodes/variables/packages/properties),
        - un XML auxiliar y un JSON genérico fuera de metadata/,
        - una carpeta metadata/ y un .jar que deben ser ignorados.
        Comprueba el conteo de taskbots, el tipo detectado y el resumen
        de archivos XML/JSON auxiliares. También valida _parse_xml_file y
        _parse_json_file sobre los archivos auxiliares generados.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "DemoProject"
            bot_dir = root / "Automation Anywhere" / "Bots" / "Demo"
            bot_dir.mkdir(parents=True, exist_ok=True)

            taskbot_path = bot_dir / "Main"
            taskbot = {
                "nodes": [],
                "variables": [],
                "packages": [{"name": "TaskBot", "version": "1.0.0"}],
                "properties": {},
                "triggers": [],
            }
            taskbot_path.write_text(json.dumps(taskbot), encoding="utf-8")

            (root / "extras").mkdir(parents=True, exist_ok=True)
            (root / "extras" / "notes.xml").write_text("<root><input Name='A' /></root>", encoding="utf-8")
            (root / "extras" / "data.json").write_text(json.dumps({"inputVars": {"A": 1}}), encoding="utf-8")
            (root / "metadata").mkdir(parents=True, exist_ok=True)
            (root / "metadata" / "ignore.json").write_text("{}", encoding="utf-8")
            (root / "skip.jar").write_text("x", encoding="utf-8")

            parsed = project_parser.parse_project(root)
            self.assertEqual(parsed["task_count"], 1)
            self.assertEqual(parsed["tasks"][0]["type"], "taskbot")
            self.assertEqual(parsed["files"]["xml_count"], 1)
            self.assertEqual(parsed["files"]["json_count"], 1)

            xml_doc = project_parser._parse_xml_file(str(root / "extras" / "notes.xml"), "extras/notes.xml")
            if xml_doc is not None:
                self.assertEqual(xml_doc["type"], "xml")

            json_doc = project_parser._parse_json_file(str(root / "extras" / "data.json"), "extras/data.json")
            if json_doc is not None:
                self.assertEqual(json_doc["type"], "json")

    def test_sdd_quality_and_file_generation(self):
        """
        Generación de SDD y reporte de calidad a partir de un project_data sintético.

        Verifica que _generate_quality_observations detecte:
        - nodos deshabilitados (código muerto),
        - try sin catch correspondiente,
        - ruta de archivo hardcodeada,
        - conexión a DB sin CredentialVault.

        Verifica que generate_sdd produzca las secciones de contratos de
        dependencias e inventario de subtasks invocadas. Comprueba además
        los helpers _describe_error_handling, _unique_preserve, _format_size
        y _generate_default_template, y que generate_sdd_file y
        generate_quality_file escriban sus archivos correctamente en disco.
        """
        project_data = {
            "name": "DemoBot",
            "tasks": [
                {
                    "name": "Main",
                    "type": "taskbot",
                    "description": "",
                    "developer": "",
                    "node_stats": {
                        "disabled_nodes": 2,
                        "total_nodes": 10,
                        "decision_nodes": 1,
                        "loop_nodes": 1,
                        "task_calls": 1,
                        "error_handlers": 0,
                    },
                    "error_handling": {"has_try": True, "has_catch": False, "has_finally": False},
                    "systems": [{"type": "file", "value": r"C:\\temp\\fixed.txt", "source": "files::open"}],
                    "task_calls": [
                        {
                            "target_name": "Lookup",
                            "inputs": [{"name": "InA", "value": "$locA$"}],
                            "outputs": [{"name": "OutB", "value": "locB"}],
                        }
                    ],
                    "variables": {
                        "input": [{"name": "InA", "type": "STRING", "default": "", "description": ""}],
                        "output": [{"name": "OutB", "type": "STRING", "default": "", "description": ""}],
                        "internal": [],
                    },
                    "dependencies": [],
                    "packages": [{"name": "TaskBot", "version": "1.0"}],
                    "size": 2048,
                    "role": "main",
                    "is_entrypoint": True,
                    "actions": ["Accion 1", "Accion 1"],
                    "comments": ["Comentario A", "Comentario A"],
                }
            ],
            "task_count": 1,
            "metadata": {"description": "", "entrypoints": ["Main"]},
            "files": {"manifest_count": 1, "xml_count": 0, "json_count": 1},
            "systems": [{"type": "database", "value": "jdbc:mysql://db.local", "source": "db::connect"}],
            "credentials": [],
            "packages": [{"name": "TaskBot", "version": "1.0"}],
        }

        quality_md = sdd_generator._generate_quality_observations(project_data)
        self.assertIn("Observaciones de Calidad - DemoBot", quality_md)
        self.assertIn("nodo(s) deshabilitado(s)", quality_md)
        self.assertIn("tiene `try` pero no `catch`", quality_md)
        self.assertIn("ruta de archivo hardcodeada", quality_md)
        self.assertIn("CredentialVault", quality_md)

        flow = {"summary": {"total_edges": 1}}
        sdd_text = sdd_generator.generate_sdd(
            project_data,
            "demo tree",
            flow,
            "![Flujo principal entre taskbots](flujo_taskbots.svg)",
        )
        self.assertIn("Contrato de Dependencias", sdd_text)
        self.assertIn("Lookup [1 in / 1 out]", sdd_text)

        self.assertEqual(sdd_generator._describe_error_handling({"has_try": True, "has_catch": True}), "try, catch")
        self.assertEqual(sdd_generator._describe_error_handling({}), "No explicito")
        self.assertEqual(sdd_generator._unique_preserve(["A", "A", " ", "B"]), ["A", "B"])
        self.assertEqual(sdd_generator._format_size(1024), "1.0KB")
        self.assertIn("SDD - {name}", sdd_generator._generate_default_template())

        with tempfile.TemporaryDirectory() as tmp_dir:
            sdd_out = Path(tmp_dir) / "docs" / "SDD_Demo.md"
            quality_out = Path(tmp_dir) / "docs" / "Calidad_Demo.md"
            saved_sdd = sdd_generator.generate_sdd_file(project_data, "demo tree", str(sdd_out), flow, "flow")
            saved_quality = sdd_generator.generate_quality_file(project_data, str(quality_out))
            self.assertTrue(Path(saved_sdd).exists())
            self.assertTrue(Path(saved_quality).exists())


if __name__ == "__main__":
    unittest.main()