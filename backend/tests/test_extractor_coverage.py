import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import app.ingestion.extractor as extractor


class ExtractorCoverageTests(unittest.TestCase):
    """
    Tests unitarios de extract_project y _validate_member_path.

    Cubren las ramas de error del extractor: archivo inexistente,
    ZIP corrupto detectado por testzip, ZIP inválido como archivo binario,
    excepción inesperada relanzada, ruta válida aceptada y path traversal
    rechazado antes de escribir en disco.
    """

    def test_extract_project_raises_file_not_found(self):
        """
        Lanza FileNotFoundError si la ruta al ZIP no existe en disco.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_zip = Path(tmp_dir) / "missing.zip"
            with self.assertRaises(FileNotFoundError):
                extractor.extract_project(missing_zip)

    def test_extract_project_raises_bad_zip_when_testzip_detects_corruption(self):
        """
        Lanza BadZipFile cuando testzip() reporta un archivo interno corrupto.

        Usa mock para simular que testzip devuelve el nombre de un archivo
        dañado sin necesidad de construir un ZIP realmente corrupto.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = Path(tmp_dir) / "project.zip"
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                zip_file.writestr("safe.txt", "ok")

            with patch("app.ingestion.extractor.zipfile.ZipFile.testzip", return_value="safe.txt"):
                with self.assertRaises(zipfile.BadZipFile):
                    extractor.extract_project(zip_path)

    def test_extract_project_re_raises_unexpected_exception(self):
        """
        Excepciones no previstas se relancean tal como llegan al llamador.

        Simula un RuntimeError en _validate_member_path para confirmar
        que el handler genérico (except Exception) del extractor no las
        absorbe silenciosamente.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = Path(tmp_dir) / "project.zip"
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                zip_file.writestr("safe.txt", "ok")

            with patch("app.ingestion.extractor._validate_member_path", side_effect=RuntimeError("boom")):
                with self.assertRaises(RuntimeError):
                    extractor.extract_project(zip_path)

    def test_extract_project_raises_bad_zip_for_invalid_archive_file(self):
        """
        Lanza BadZipFile si el archivo en disco no es un ZIP válido.

        Escribe texto plano en la ruta del ZIP para que zipfile.ZipFile
        falle al intentar leer la firma del archivo.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = Path(tmp_dir) / "invalid.zip"
            zip_path.write_text("this is not a zip", encoding="utf-8")

            with self.assertRaises(zipfile.BadZipFile):
                extractor.extract_project(zip_path)

    def test_extract_project_raises_when_uncompressed_size_exceeds_limit(self):
        """
        Lanza ValueError cuando el total descomprimido supera MAX_EXTRACTION_SIZE.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = Path(tmp_dir) / "project.zip"
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                zip_file.writestr("big.txt", "1234567890")

            with patch("app.ingestion.extractor.MAX_EXTRACTION_SIZE", 5):
                with self.assertRaises(ValueError):
                    extractor.extract_project(zip_path)

    def test_validate_member_path_allows_safe_relative_paths(self):
        """
        _validate_member_path no lanza nada para rutas relativas seguras.

        Una ruta como 'folder/safe.txt' está dentro del directorio destino
        y debe pasar sin excepción.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "extracted"
            target.mkdir(parents=True, exist_ok=True)
            extractor._validate_member_path("folder/safe.txt", target)

    def test_validate_member_path_rejects_path_traversal(self):
        """
        _validate_member_path lanza ValueError para path traversal.

        Una entrada '../escape.txt' resuelve fuera del directorio destino;
        la función debe detectarlo y lanzar ValueError antes de extraer.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "extracted"
            target.mkdir(parents=True, exist_ok=True)
            with self.assertRaises(ValueError):
                extractor._validate_member_path("../escape.txt", target)


if __name__ == "__main__":
    unittest.main()