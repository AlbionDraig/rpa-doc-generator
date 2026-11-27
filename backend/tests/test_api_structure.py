# Explicit seams help future refactors.
import unittest

from app.main import app


class ApiStructureTests(unittest.TestCase):
    def _route_exists(self, path, method):
        # Use the public OpenAPI schema: since FastAPI 0.16x included routers are
        # no longer flattened into app.routes, so walking routes is version-fragile.
        operations = app.openapi().get("paths", {}).get(path, {})
        return method.lower() in operations

    def test_system_endpoints_are_available(self):
        self.assertTrue(self._route_exists("/", "GET"))
        self.assertTrue(self._route_exists("/health", "GET"))

    def test_required_upload_endpoints_exist(self):
        self.assertTrue(self._route_exists("/generate/", "POST"))
        self.assertTrue(self._route_exists("/quality/", "POST"))

    def test_download_route_exists(self):
        self.assertTrue(self._route_exists("/download/{session_id}/{file_type}", "GET"))


if __name__ == "__main__":
    unittest.main()
