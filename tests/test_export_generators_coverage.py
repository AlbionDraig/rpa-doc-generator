import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.generator import pdf_generator, word_generator


_MIN_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5mN2QAAAAASUVORK5CYII="
)


def _tiny_png_bytes():
    return base64.b64decode(_MIN_PNG_B64)


class _FakePisaStatus:
    def __init__(self, err=0):
        self.err = err


class ExportGeneratorsCoverageTests(unittest.TestCase):
    def _project_data(self):
        return {
            "name": "DemoBot",
            "metadata": {"description": "Demo desc", "entrypoints": ["Main"]},
            "files": {"manifest_count": 1, "xml_count": 1, "json_count": 2},
            "systems": [
                {"type": "database", "value": "jdbc:mysql://db", "source": "Main"},
                {"type": "file", "value": "C:/hardcoded/path.txt", "source": "Main"},
            ],
            "credentials": [
                {
                    "credential_name": "AA360_LOGIN",
                    "attribute": "password",
                    "vault": "Default",
                    "source": "Main",
                }
            ],
            "packages": [{"name": "Browser", "version": "1.0"}],
            "task_count": 1,
            "tasks": [
                {
                    "name": "Main",
                    "type": "taskbot",
                    "role": "main",
                    "path": "Automation Anywhere/Bots/Main",
                    "is_entrypoint": True,
                    "size": 1024,
                    "description": "Task principal",
                    "developer": "QA",
                    "declared_date": "2026-04-16",
                    "node_stats": {
                        "total_nodes": 10,
                        "decision_nodes": 1,
                        "loop_nodes": 1,
                        "task_calls": 1,
                        "error_handlers": 1,
                        "disabled_nodes": 1,
                    },
                    "error_handling": {"has_try": True, "has_catch": False, "has_finally": True},
                    "dependencies": [{"name": "Lookup", "type": "runTask"}],
                    "task_calls": [
                        {
                            "target_name": "Lookup",
                            "inputs": [{"name": "InCustomer", "value": "$Cust$"}],
                            "outputs": [{"name": "OutStatus", "value": "$Status$"}],
                        }
                    ],
                    "packages": [{"name": "Browser", "version": "1.0"}],
                    "actions": ["Abrir portal", "Consultar", "Consultar"],
                    "comments": ["Comentario A", "Comentario A", "Comentario B"],
                    "systems": [
                        {"type": "url", "value": "https://example.com"},
                        {"type": "file", "value": "C:/hardcoded/path.txt"},
                    ],
                    "variables": {
                        "input": [
                            {
                                "name": "InCustomer",
                                "type": "STRING",
                                "default": "",
                                "description": "cliente",
                            }
                        ],
                        "output": [
                            {
                                "name": "OutStatus",
                                "type": "STRING",
                                "default": "",
                                "description": "estado",
                            }
                        ],
                        "internal": [
                            {
                                "name": "Tmp",
                                "type": "STRING",
                                "scope": "local",
                                "default": "",
                            }
                        ],
                    },
                }
            ],
        }

    def test_word_generators_create_files(self):
        data = self._project_data()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            flow_png = temp_path / "flow.png"
            flow_png.write_bytes(_tiny_png_bytes())

            sdd_docx = temp_path / "SDD_Demo.docx"
            quality_docx = temp_path / "Calidad_Demo.docx"

            sdd_result = word_generator.generate_sdd_word(
                data,
                "root\n|-- Main",
                str(sdd_docx),
                flow={"summary": {"total_edges": 1}},
                flow_image_path=str(flow_png),
            )
            quality_result = word_generator.generate_quality_word(data, str(quality_docx))

            self.assertEqual(sdd_result, str(sdd_docx))
            self.assertEqual(quality_result, str(quality_docx))
            self.assertTrue(sdd_docx.exists())
            self.assertTrue(quality_docx.exists())

    def test_word_helpers_and_observations(self):
        self.assertEqual(word_generator._format_size(None), "0B")
        self.assertEqual(word_generator._describe_error_handling({}), "No explicito")
        self.assertEqual(word_generator._describe_error_handling({"has_try": True, "has_catch": True}), "try, catch")
        self.assertEqual(word_generator._unique_preserve(["a", "a", "", " b "]), ["a", "b"])

        no_obs = word_generator._collect_quality_observations(
            {"tasks": [{"name": "Main", "type": "taskbot", "description": "ok", "developer": "dev", "systems": [], "node_stats": {}, "error_handling": {"has_try": True, "has_catch": True}}], "systems": [], "credentials": [{"credential_name": "x"}]}
        )
        self.assertEqual(no_obs, [])

        data = self._project_data()
        obs = word_generator._collect_quality_observations(data)
        self.assertTrue(any("deshabilitado" in item for item in obs))
        self.assertTrue(any("try pero no catch" in item for item in obs))
        self.assertTrue(any("hardcodeada" in item for item in obs))

    def test_pdf_helpers_and_generators(self):
        self.assertEqual(pdf_generator._escape_html("<a&b>"), "&lt;a&amp;b&gt;")
        self.assertIn("[DIR]", pdf_generator._sanitize_tree_for_pdf("📁 folder"))
        self.assertIn("<br/>", pdf_generator._fix_pre_newlines("<pre><code>a\nb</code></pre>"))
        self.assertIn("<a name=\"x\"></a>", pdf_generator._fix_heading_anchors('<h2 id="x">Title</h2>'))

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            flow_png = temp_path / "flow.png"
            flow_png.write_bytes(_tiny_png_bytes())

            sdd_pdf = temp_path / "SDD_Demo.pdf"
            quality_pdf = temp_path / "Calidad_Demo.pdf"
            captured_html = []

            def fake_create_pdf(html, dest, encoding):
                captured_html.append(html)
                dest.write(b"%PDF")
                return _FakePisaStatus(err=1)

            with patch("app.generator.pdf_generator.pisa.CreatePDF", side_effect=fake_create_pdf), patch(
                "app.generator.pdf_generator.markdown.markdown",
                return_value='<h1 id="sec">Title</h1><pre><code>a\nb</code></pre><img src="flujo_taskbots.svg"/>',
            ):
                sdd_result = pdf_generator.generate_sdd_pdf(
                    "# demo",
                    str(sdd_pdf),
                    project_name="Demo & <Bot>",
                    flow_image_path=str(flow_png),
                )
                quality_result = pdf_generator.generate_quality_pdf("# quality", str(quality_pdf), project_name="Demo")

            self.assertEqual(sdd_result, str(sdd_pdf))
            self.assertEqual(quality_result, str(quality_pdf))
            self.assertTrue(sdd_pdf.exists())
            self.assertTrue(quality_pdf.exists())
            self.assertTrue(any("data:image/png;base64" in html for html in captured_html))
            self.assertTrue(any("Reporte de Calidad" in html for html in captured_html))

    def test_pdf_generators_raise_on_error(self):
        with patch("app.generator.pdf_generator.markdown.markdown", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                pdf_generator.generate_sdd_pdf("# x", "out.pdf")
            with self.assertRaises(RuntimeError):
                pdf_generator.generate_quality_pdf("# x", "out.pdf")


if __name__ == "__main__":
    unittest.main()
