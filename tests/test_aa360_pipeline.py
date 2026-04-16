import json
import shutil
import unittest
import uuid
import zipfile
from contextlib import contextmanager
from pathlib import Path

from app.analysis.flow_builder import build_flow
from app.generator.diagram_generator import generate_flow_svg
from app.generator.sdd_generator import generate_sdd
from app.ingestion.extractor import extract_project
from app.parser.project_parser import parse_project

TEST_TMP_ROOT = Path("tests") / ".tmp"
TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)


class AA360PipelineTests(unittest.TestCase):
    """
    Tests de integración del pipeline completo de AA360.

    Verifican que las etapas de parseo, construcción de flujo, generación
    de SVG y compilación del SDD se ejecuten de extremo a extremo sobre un
    proyecto sintético con estructura real de AA360 (manifest.json +
    taskbots JSON).
    """

    def test_parse_project_and_flow_use_real_taskbot_dependencies(self):
        """
        Pipeline completo: parseo → flujo → SVG → SDD.

        Construye un proyecto de 2 taskbots (Main → Lookup) con manifest.json
        y un contrato de variables (InCustomer / OutStatus). Verifica:
        - conteo de tareas y orden de aparición,
        - entrypoint detectado correctamente,
        - arista de flujo con etiqueta 'runTask',
        - contenido del SVG y del documento SDD generado,
        - variables input/output del taskbot Lookup.
        """
        with self._workspace_temp_dir() as temp_dir:
            project_root = Path(temp_dir) / "DemoProject"
            self._create_demo_project(project_root)

            project_data = parse_project(project_root)
            flow = build_flow(project_data["tasks"])
            svg = generate_flow_svg(flow)
            sdd = generate_sdd(
                project_data,
                "demo tree",
                flow,
                "![Flujo principal entre taskbots](flujo_taskbots.svg)",
            )

            self.assertEqual(project_data["task_count"], 2)
            self.assertEqual([task["name"] for task in project_data["tasks"]], ["Main", "Lookup"])
            self.assertEqual(project_data["metadata"]["entrypoints"], ["Main"])
            self.assertEqual(flow["summary"]["total_edges"], 1)
            self.assertEqual(flow["edges"][0]["label"], "runTask")
            self.assertIn("<svg", svg)
            self.assertIn("Flujo principal entre taskbots", svg)
            self.assertIn("flujo_taskbots.svg", sdd)
            self.assertIn("Subtasks invocadas", sdd)
            self.assertIn("Lookup [1 in / 1 out]", sdd)

            lookup_task = project_data["tasks"][1]
            self.assertEqual([variable["name"] for variable in lookup_task["variables"]["input"]], ["InCustomer"])
            self.assertEqual([variable["name"] for variable in lookup_task["variables"]["output"]], ["OutStatus"])

    def test_extract_project_rejects_zip_traversal(self):
        """
        Seguridad: el extractor debe rechazar ZIPs con path traversal.

        Crea un ZIP malicioso con una entrada '../escape.txt' y confirma
        que extract_project lanza ValueError antes de escribir ningún
        archivo fuera del directorio de destino.
        """
        with self._workspace_temp_dir() as temp_dir:
            zip_path = Path(temp_dir) / "bad.zip"
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                zip_file.writestr("../escape.txt", "boom")

            with self.assertRaises(ValueError):
                extract_project(zip_path)

    def _create_demo_project(self, project_root):
        main_path = project_root / "Automation Anywhere" / "Bots" / "Demo" / "Main"
        subtask_path = project_root / "Automation Anywhere" / "Bots" / "Demo" / "Subtasks" / "Lookup"
        main_path.parent.mkdir(parents=True, exist_ok=True)
        subtask_path.parent.mkdir(parents=True, exist_ok=True)

        manifest = {
            "files": [
                {
                    "path": r"Automation Anywhere\Bots\Demo\Main",
                    "contentType": "application/vnd.aa.taskbot",
                    "manualDependencies": [],
                    "scannedDependencies": [r"Automation Anywhere\Bots\Demo\Subtasks\Lookup"],
                },
                {
                    "path": r"Automation Anywhere\Bots\Demo\Subtasks\Lookup",
                    "contentType": "application/vnd.aa.taskbot",
                    "manualDependencies": [],
                    "scannedDependencies": [],
                },
            ],
            "packages": [
                {"name": "TaskBot", "version": "1.0.0"},
                {"name": "String", "version": "1.0.0"},
            ],
        }
        self._write_json(project_root / "manifest.json", manifest)

        main_task = {
            "triggers": [],
            "nodes": [
                self._comment_node("Developer: QA"),
                self._comment_node("Descripcion: Demo flow"),
                {
                    "uid": "node-run-task",
                    "commandName": "runTask",
                    "packageName": "TaskBot",
                    "disabled": False,
                    "attributes": [
                        {
                            "name": "taskbot",
                            "value": {
                                "type": "TASKBOT",
                                "taskbotFile": {
                                    "type": "FILE",
                                    "string": "repository:///Automation%20Anywhere/Bots/Demo/Subtasks/Lookup",
                                },
                                "taskbotInput": {
                                    "type": "DICTIONARY",
                                    "dictionary": [
                                        {
                                            "key": "InCustomer",
                                            "value": {"type": "STRING", "expression": "$LocCustomer$"},
                                        }
                                    ],
                                },
                            },
                        }
                    ],
                    "returnTo": {
                        "type": "DICTIONARY",
                        "dictionary": [
                            {
                                "key": "OutStatus",
                                "value": {"type": "VARIABLE", "variableName": "LocStatus"},
                            }
                        ],
                    },
                },
            ],
            "variables": [
                {
                    "name": "LocCustomer",
                    "type": "STRING",
                    "description": "",
                    "readOnly": False,
                    "input": False,
                    "output": False,
                    "defaultValue": {"type": "STRING", "string": ""},
                },
                {
                    "name": "LocStatus",
                    "type": "STRING",
                    "description": "",
                    "readOnly": False,
                    "input": False,
                    "output": False,
                    "defaultValue": {"type": "STRING", "string": ""},
                },
            ],
            "packages": [{"name": "TaskBot", "version": "1.0.0"}],
            "properties": {"timeout": "0s"},
        }

        subtask = {
            "triggers": [],
            "nodes": [
                self._comment_node("Developer: QA"),
                self._comment_node("Descripcion: Demo lookup"),
            ],
            "variables": [
                {
                    "name": "InCustomer",
                    "type": "STRING",
                    "description": "Customer id",
                    "readOnly": False,
                    "input": True,
                    "output": False,
                    "defaultValue": {"type": "STRING", "string": ""},
                },
                {
                    "name": "OutStatus",
                    "type": "STRING",
                    "description": "Lookup result",
                    "readOnly": False,
                    "input": False,
                    "output": True,
                    "defaultValue": {"type": "STRING", "string": ""},
                },
            ],
            "packages": [{"name": "String", "version": "1.0.0"}],
            "properties": {"timeout": "0s"},
        }

        self._write_json(main_path, main_task)
        self._write_json(subtask_path, subtask)

    def _comment_node(self, text):
        return {
            "uid": text,
            "commandName": "Comment",
            "packageName": "Comment",
            "disabled": False,
            "attributes": [{"name": "comment", "value": {"type": "STRING", "string": text}}],
        }

    def _write_json(self, path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file_obj:
            json.dump(payload, file_obj)

    @contextmanager
    def _workspace_temp_dir(self):
        temp_dir = TEST_TMP_ROOT / f"run_{uuid.uuid4().hex}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
