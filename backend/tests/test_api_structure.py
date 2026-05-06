import unittest

from app.main import app


class ApiStructureTests(unittest.TestCase):
    def _route_exists(self, path, method):
        target_method = method.upper()
        for route in app.routes:
            methods = getattr(route, "methods", set())
            if route.path == path and target_method in methods:
                return True
        return False

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
