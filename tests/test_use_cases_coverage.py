import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.application.use_cases.download_artifact import _first_match, resolve_download_file
from app.application.use_cases.generate_quality import run_generate_quality
from app.application.use_cases.generate_sdd import run_generate_sdd


class _DummyLogger:
    def info(self, *args, **kwargs):
        return None


class _DummyUpload:
    def __init__(self, filename="demo.zip"):
        self.filename = filename


class _FixedNow:
    def strftime(self, _):
        return "20260416_130000_000000"


class _FixedDateTime:
    @staticmethod
    def now():
        return _FixedNow()


class UseCasesCoverageTests(unittest.TestCase):
    def test_run_generate_sdd_happy_path_and_removes_png(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = SimpleNamespace(output_dir=Path(temp_dir))
            logger = _DummyLogger()
            file_obj = _DummyUpload()

            def fake_convert(_svg_path, png_path):
                Path(png_path).write_bytes(b"png")

            with patch("app.application.use_cases.generate_sdd.datetime", _FixedDateTime), patch(
                "app.application.use_cases.generate_sdd.save_file", return_value="/tmp/demo.zip"
            ), patch("app.application.use_cases.generate_sdd.extract_project", return_value="/tmp/project"), patch(
                "app.application.use_cases.generate_sdd.parse_project",
                return_value={"name": "Demo", "task_count": 1, "tasks": [{"name": "Main"}]},
            ), patch("app.application.use_cases.generate_sdd.build_flow", return_value={"nodes": [], "edges": []}), patch(
                "app.application.use_cases.generate_sdd.build_tree", return_value="tree"
            ), patch("app.application.use_cases.generate_sdd.generate_flow_svg", return_value="<svg/>"), patch(
                "app.application.use_cases.generate_sdd.convert_svg_to_png", side_effect=fake_convert
            ), patch("app.application.use_cases.generate_sdd.generate_sdd", return_value="# demo"), patch(
                "app.application.use_cases.generate_sdd.generate_sdd_file"
            ), patch("app.application.use_cases.generate_sdd.generate_sdd_word"), patch(
                "app.application.use_cases.generate_sdd.generate_sdd_pdf"
            ):
                result = run_generate_sdd(file_obj, settings, logger)

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["session_id"], "20260416_130000_000000")
            self.assertTrue(result["archivos_salida"]["flujo_svg_path"].endswith("flujo_taskbots.svg"))
            self.assertFalse(
                Path(result["output_directory"]).joinpath("flujo_taskbots.png").exists(),
                "El PNG intermedio debe eliminarse al finalizar",
            )

    def test_run_generate_quality_reads_generated_markdown(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = SimpleNamespace(output_dir=Path(temp_dir))
            logger = _DummyLogger()
            file_obj = _DummyUpload()

            def fake_generate_quality_file(_project_data, output_path):
                Path(output_path).write_text("# Calidad", encoding="utf-8")

            with patch("app.application.use_cases.generate_quality.datetime", _FixedDateTime), patch(
                "app.application.use_cases.generate_quality.save_file", return_value="/tmp/demo.zip"
            ), patch("app.application.use_cases.generate_quality.extract_project", return_value="/tmp/project"), patch(
                "app.application.use_cases.generate_quality.parse_project", return_value={"name": "Demo"}
            ), patch(
                "app.application.use_cases.generate_quality.generate_quality_file",
                side_effect=fake_generate_quality_file,
            ), patch("app.application.use_cases.generate_quality.generate_quality_word"), patch(
                "app.application.use_cases.generate_quality.generate_quality_pdf"
            ) as pdf_mock:
                result = run_generate_quality(file_obj, settings, logger)

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["session_id"], "20260416_130000_000000")
            self.assertTrue(result["archivos_salida"]["calidad_path"].endswith("Calidad_Demo.md"))
            self.assertEqual(pdf_mock.call_count, 1)

    def test_download_artifact_resolution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "SDD_Demo.md").write_text("x", encoding="utf-8")

            self.assertTrue(_first_match(output_dir, "SDD_*.md").name.startswith("SDD_"))
            self.assertIsNone(_first_match(output_dir, "Nope_*.md"))
            self.assertIsNone(resolve_download_file(output_dir, "invalid"))

            resolved = resolve_download_file(output_dir, "sdd")
            self.assertEqual(resolved.name, "SDD_Demo.md")


if __name__ == "__main__":
    unittest.main()
