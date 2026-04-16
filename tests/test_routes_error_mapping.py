import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.routes.download import download_file
from app.api.routes.generate import generate
from app.api.routes.quality import quality
from app.api.routes.system import health, root


class _DummyLogger:
    def info(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None

    def error(self, *args, **kwargs):
        return None


class _DummyUpload:
    def __init__(self, filename="demo.zip"):
        self.filename = filename


class RoutesErrorMappingTests(unittest.TestCase):
    def _run(self, coro):
        return asyncio.run(coro)

    def _request_with_settings(self, output_dir):
        settings = SimpleNamespace(
            output_dir=Path(output_dir),
            app_title="RPA Doc Generator",
            app_version="1.0.0",
            public_base_url="http://localhost:8000",
        )
        return SimpleNamespace(state=SimpleNamespace(settings=settings, logger=_DummyLogger()))

    def test_generate_maps_known_errors(self):
        request = SimpleNamespace(app=self._request_with_settings(tempfile.gettempdir()))
        file_obj = _DummyUpload()

        with patch("app.api.routes.generate.run_generate_sdd", side_effect=ValueError("bad")):
            with self.assertRaises(HTTPException) as ctx:
                self._run(generate(file_obj, request))
            self.assertEqual(ctx.exception.status_code, 400)

        with patch("app.api.routes.generate.run_generate_sdd", side_effect=FileNotFoundError("x")):
            with self.assertRaises(HTTPException) as ctx:
                self._run(generate(file_obj, request))
            self.assertEqual(ctx.exception.status_code, 404)

        with patch("app.api.routes.generate.run_generate_sdd", side_effect=RuntimeError("boom")):
            with self.assertRaises(HTTPException) as ctx:
                self._run(generate(file_obj, request))
            self.assertEqual(ctx.exception.status_code, 500)

    def test_quality_maps_known_errors(self):
        request = SimpleNamespace(app=self._request_with_settings(tempfile.gettempdir()))
        file_obj = _DummyUpload()

        with patch("app.api.routes.quality.run_generate_quality", side_effect=ValueError("bad")):
            with self.assertRaises(HTTPException) as ctx:
                self._run(quality(file_obj, request))
            self.assertEqual(ctx.exception.status_code, 400)

        with patch("app.api.routes.quality.run_generate_quality", side_effect=FileNotFoundError("x")):
            with self.assertRaises(HTTPException) as ctx:
                self._run(quality(file_obj, request))
            self.assertEqual(ctx.exception.status_code, 404)

        with patch("app.api.routes.quality.run_generate_quality", side_effect=RuntimeError("boom")):
            with self.assertRaises(HTTPException) as ctx:
                self._run(quality(file_obj, request))
            self.assertEqual(ctx.exception.status_code, 500)

    def test_download_maps_errors_and_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            request = SimpleNamespace(app=self._request_with_settings(temp_dir))

            with patch("app.api.routes.download.resolve_download_file", return_value=None):
                with self.assertRaises(HTTPException) as ctx:
                    self._run(download_file("s1", "invalid", request))
                self.assertEqual(ctx.exception.status_code, 400)

            with patch(
                "app.api.routes.download.resolve_download_file",
                return_value=Path(temp_dir) / "s1" / "missing.md",
            ):
                with self.assertRaises(HTTPException) as ctx:
                    self._run(download_file("s1", "sdd", request))
                self.assertEqual(ctx.exception.status_code, 404)

            with patch("app.api.routes.download.resolve_download_file", side_effect=RuntimeError("boom")):
                with self.assertRaises(HTTPException) as ctx:
                    self._run(download_file("s1", "sdd", request))
                self.assertEqual(ctx.exception.status_code, 500)

            session_dir = Path(temp_dir) / "s1"
            session_dir.mkdir(parents=True, exist_ok=True)
            existing_file = session_dir / "SDD_Demo.md"
            existing_file.write_text("demo", encoding="utf-8")

            with patch("app.api.routes.download.resolve_download_file", return_value=existing_file):
                response = self._run(download_file("s1", "sdd", request))
                self.assertEqual(getattr(response, "status_code", 200), 200)

    def test_system_routes_return_expected_payload(self):
        request = SimpleNamespace(app=self._request_with_settings(tempfile.gettempdir()))

        root_payload = self._run(root(request))
        health_payload = self._run(health(request))

        self.assertEqual(root_payload["message"], "RPA Doc Generator API")
        self.assertTrue(root_payload["docs"].endswith("/docs"))
        self.assertEqual(health_payload["status"], "healthy")
        self.assertEqual(health_payload["version"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
