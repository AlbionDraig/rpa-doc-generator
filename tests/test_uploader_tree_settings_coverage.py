import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.analysis.tree_builder import _detect_file_kind, _format_size, build_tree, should_exclude
from app.application.settings import AppSettings, _env_int
from app.ingestion import uploader


class _DummyUpload:
    def __init__(self, filename, content):
        self.filename = filename
        self.file = io.BytesIO(content)


class UploaderTreeSettingsCoverageTests(unittest.TestCase):
    def test_save_file_success_invalid_and_limits(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(uploader, "TMP_DIR", Path(temp_dir)), patch.object(
                uploader, "MAX_FILE_SIZE", 8
            ), patch.object(uploader, "CHUNK_SIZE", 4):
                with self.assertRaises(ValueError):
                    uploader.save_file(_DummyUpload("demo.txt", b"zip"))

                saved = uploader.save_file(_DummyUpload("demo.zip", b"1234"))
                self.assertTrue(Path(saved).exists())

                with self.assertRaises(ValueError):
                    uploader.save_file(_DummyUpload("big.zip", b"123456789"))

                with self.assertRaises(ValueError):
                    uploader.save_file(_DummyUpload("empty.zip", b""))

    def test_build_tree_and_helpers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "visible").mkdir()
            (root / "visible" / "task.json").write_text("{}", encoding="utf-8")
            (root / "visible" / "table.csv").write_text("a,b", encoding="utf-8")
            (root / "metadata").mkdir()
            (root / "hidden.tmp").write_text("x", encoding="utf-8")
            (root / ".git").mkdir()
            (root / "classfile.class").write_text("x", encoding="utf-8")

            tree_with_stats = build_tree(str(root), include_stats=True)
            tree_no_stats = build_tree(str(root), include_stats=False)

            self.assertIn("visible/", tree_with_stats)
            self.assertIn("[JSON] task.json", tree_with_stats)
            self.assertIn("[CSV] table.csv", tree_with_stats)
            self.assertNotIn("metadata", tree_with_stats)
            self.assertNotIn(".git", tree_with_stats)
            self.assertNotIn("(", tree_no_stats)

            self.assertTrue(should_exclude("metadata"))
            self.assertTrue(should_exclude(".env"))
            self.assertTrue(should_exclude("x.class"))
            self.assertFalse(should_exclude("task.json"))

            self.assertEqual(_detect_file_kind("data.xml"), "📝 [XML]")
            self.assertEqual(_detect_file_kind("sheet.xlsx"), "📊 [EXCEL]")
            self.assertEqual(_detect_file_kind("Main"), "🤖 [BOT]")
            self.assertEqual(_detect_file_kind("notes.txt"), "📄 [FILE]")
            self.assertEqual(_format_size(100), "100.0B")

            error_tree = build_tree(str(root / "missing"))
            self.assertTrue(error_tree.startswith("Error:"))

    def test_settings_parsing_from_env(self):
        with patch.dict(
            "os.environ",
            {
                "APP_PORT": "9000",
                "APP_ACCESS_LOG": "no",
                "CORS_ORIGINS": "http://a.com, http://b.com",
                "PUBLIC_BASE_URL": "http://example.com/",
            },
            clear=False,
        ):
            settings = AppSettings.from_env()

        self.assertEqual(settings.app_port, 9000)
        self.assertFalse(settings.app_access_log)
        self.assertEqual(settings.cors_origins, ["http://a.com", "http://b.com"])
        self.assertEqual(settings.public_base_url, "http://example.com")

        with patch.dict("os.environ", {"APP_PORT": "9000"}, clear=False):
            self.assertEqual(_env_int("APP_PORT", "8000"), 9000)

        with patch.dict("os.environ", {"APP_PORT": "bad"}, clear=False):
            self.assertEqual(_env_int("APP_PORT", "8000"), 8000)


if __name__ == "__main__":
    unittest.main()
