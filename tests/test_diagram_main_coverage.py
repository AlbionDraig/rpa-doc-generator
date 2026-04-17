import asyncio
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Mapping, cast
from unittest.mock import patch
import types

from fastapi import Request

from app.generator import diagram_generator
from app import main as main_module
from app.api.deps import get_logger
from app.observability import ContextLoggerAdapter, ObservabilityMiddleware


class _DummyDrawing:
    def __init__(self):
        self.width = 100
        self.height = 50
        self.scaled = []

    def scale(self, x, y):
        self.scaled.append((x, y))


class DiagramAndMainCoverageTests(unittest.TestCase):
    def _run(self, coro):
        return asyncio.run(coro)

    def test_diagram_helpers(self):
        self.assertEqual(diagram_generator._blend_color("#000000", 0, "#ffffff"), "#ffffff")
        self.assertEqual(diagram_generator._blend_color("#000000", 1, "#ffffff"), "#000000")

        wrapped = diagram_generator._wrap_text("uno dos tres cuatro cinco", 8, 2)
        self.assertEqual(len(wrapped), 2)
        self.assertTrue(wrapped[-1].endswith("...") or len(" ".join(wrapped).split()) >= 5)

        self.assertEqual(diagram_generator._build_edge_label({"label": "runTask"}), "runTask")
        self.assertIn("in /", diagram_generator._build_edge_label({"label": "runTask", "inputs_count": 1, "outputs_count": 2}))

        empty = diagram_generator._empty_svg("Nada")
        self.assertIn("Nada", empty)
        self.assertIn("<svg", empty)

    def test_generate_flow_svg_variants(self):
        svg_empty = diagram_generator.generate_flow_svg({"nodes": [], "edges": []})
        self.assertIn("No hay taskbots detectados", svg_empty)

        flow = {
            "nodes": [
                {"id": "task_1", "name": "Main", "path": "A/Main", "role": "main", "is_entrypoint": True, "type": "taskbot", "node_count": 3},
                {"id": "task_2", "name": "Lookup", "path": "A/Lookup", "role": "subtask", "is_entrypoint": False, "type": "taskbot", "node_count": 1},
            ],
            "edges": [{"from": "task_1", "to": "task_2", "label": "runTask", "inputs_count": 1, "outputs_count": 1}],
        }
        svg = diagram_generator.generate_flow_svg(flow)
        self.assertIn("Flujo principal entre taskbots", svg)
        self.assertIn("runTask | 1 in / 1 out", svg)
        self.assertIn("Inicio", svg)

    def test_convert_svg_to_png_branches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            svg_path = Path(temp_dir) / "flow.svg"
            png_path = Path(temp_dir) / "flow.png"
            svg_path.write_text("<svg/>", encoding="utf-8")

            drawing = _DummyDrawing()
            with patch("svglib.svglib.svg2rlg", return_value=drawing), patch(
                "reportlab.graphics.renderPM.drawToFile"
            ) as draw_mock:
                result = diagram_generator.convert_svg_to_png(svg_path, png_path, scale=2.0)
                self.assertEqual(result, str(png_path))
                self.assertEqual(drawing.scaled, [(2.0, 2.0)])
                self.assertEqual(draw_mock.call_count, 1)

            with patch("svglib.svglib.svg2rlg", return_value=None):
                self.assertIsNone(diagram_generator.convert_svg_to_png(svg_path, png_path))

            with patch("svglib.svglib.svg2rlg", side_effect=RuntimeError("boom")):
                self.assertIsNone(diagram_generator.convert_svg_to_png(svg_path, png_path))

    def test_main_custom_docs_and_create_app(self):
        docs = self._run(main_module.custom_swagger_ui_html())
        redoc = self._run(main_module.redoc_html())
        oauth = self._run(main_module.swagger_ui_redirect())
        self.assertTrue(hasattr(docs, "body"))
        self.assertTrue(hasattr(redoc, "body"))
        self.assertTrue(hasattr(oauth, "body"))

        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            static_dir = base / "static"
            static_dir.mkdir(parents=True, exist_ok=True)
            (static_dir / "favicon.ico").write_bytes(b"ico")

            custom_settings = SimpleNamespace(
                app_title="RPA Doc Generator",
                app_description="Demo",
                app_version="1.0.0",
                cors_origins=["http://localhost"],
                output_dir=base / "out",
                tmp_dir=base / "tmp",
                static_dir=static_dir,
                app_host="0.0.0.0",
                app_port=8000,
                app_log_level="info",
                app_access_log=True,
                api_rate_limit_enabled=True,
                api_rate_limit_max_requests=30,
                api_rate_limit_window_seconds=60,
                max_concurrent_generations=2,
                generation_acquire_timeout_seconds=10,
            )

            with patch.object(main_module, "settings", custom_settings):
                app_instance = main_module.create_app()
                self.assertTrue(custom_settings.output_dir.exists())
                self.assertTrue(custom_settings.tmp_dir.exists())
                self.assertEqual(app_instance.state.settings.app_title, "RPA Doc Generator")
                self.assertTrue(
                    any(layer.cls is ObservabilityMiddleware for layer in app_instance.user_middleware)
                )

    def test_get_logger_returns_context_adapter(self):
        base_logger = SimpleNamespace(info=lambda *args, **kwargs: None)
        request = cast(
            Request,
            SimpleNamespace(
                app=SimpleNamespace(state=SimpleNamespace(logger=base_logger)),
                state=SimpleNamespace(request_id="req-123"),
                method="POST",
                url=SimpleNamespace(path="/generate/"),
            ),
        )

        logger = get_logger(request)
        extra = cast(Mapping[str, object], logger.extra)

        self.assertIsInstance(logger, ContextLoggerAdapter)
        self.assertEqual(extra["request_id"], "req-123")
        self.assertEqual(extra["http_method"], "POST")
        self.assertEqual(extra["http_path"], "/generate/")

    def test_main_dunder_main_runs_uvicorn(self):
        calls = []

        def _fake_run(*args, **kwargs):
            calls.append((args, kwargs))

        fake_uvicorn = types.SimpleNamespace(run=_fake_run)
        previous_main_module = sys.modules.pop("app.main", None)
        try:
            with patch.dict("sys.modules", {"uvicorn": fake_uvicorn}):
                runpy.run_module("app.main", run_name="__main__")
        finally:
            if previous_main_module is not None:
                sys.modules["app.main"] = previous_main_module

        self.assertTrue(calls)
        self.assertIn("host", calls[0][1])
        self.assertIn("port", calls[0][1])


if __name__ == "__main__":
    unittest.main()
