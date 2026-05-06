import asyncio
import unittest
from types import SimpleNamespace
from typing import cast

from fastapi import Request

from app.api.deps import get_generation_limiter


class ApiDepsFallbackCoverageTests(unittest.TestCase):
    def test_get_generation_limiter_falls_back_without_app_state(self):
        request = cast(Request, SimpleNamespace(app=None))
        limiter = get_generation_limiter(request)

        async def scenario():
            async with limiter.slot() as acquired:
                self.assertTrue(acquired)

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
