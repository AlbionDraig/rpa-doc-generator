import asyncio
import unittest

from app.limits import ConcurrencyLimiter, NoopConcurrencyLimiter, SlidingWindowRateLimiter


class LimitsCoverageTests(unittest.TestCase):
    def test_sliding_window_rate_limiter_allows_then_blocks(self):
        limiter = SlidingWindowRateLimiter(limit=2, window_seconds=10)

        allowed_1, retry_1, remaining_1 = limiter.check("ip:/generate", now=100.0)
        allowed_2, retry_2, remaining_2 = limiter.check("ip:/generate", now=101.0)
        allowed_3, retry_3, remaining_3 = limiter.check("ip:/generate", now=102.0)

        self.assertTrue(allowed_1)
        self.assertEqual(retry_1, 0)
        self.assertEqual(remaining_1, 1)

        self.assertTrue(allowed_2)
        self.assertEqual(retry_2, 0)
        self.assertEqual(remaining_2, 0)

        self.assertFalse(allowed_3)
        self.assertGreaterEqual(retry_3, 1)
        self.assertEqual(remaining_3, 0)

    def test_sliding_window_rate_limiter_recovers_after_window(self):
        limiter = SlidingWindowRateLimiter(limit=1, window_seconds=5)

        allowed_1, _, _ = limiter.check("ip:/quality", now=100.0)
        allowed_2, _, _ = limiter.check("ip:/quality", now=106.0)

        self.assertTrue(allowed_1)
        self.assertTrue(allowed_2)

    def test_concurrency_limiter_timeout_branch(self):
        async def _scenario():
            limiter = ConcurrencyLimiter(limit=1, acquire_timeout_seconds=0.01)
            async with limiter.slot() as acquired_first:
                self.assertTrue(acquired_first)
                async with limiter.slot() as acquired_second:
                    self.assertFalse(acquired_second)

        asyncio.run(_scenario())

    def test_noop_limiter_always_allows(self):
        async def _scenario():
            limiter = NoopConcurrencyLimiter()
            async with limiter.slot() as acquired:
                self.assertTrue(acquired)

        asyncio.run(_scenario())


if __name__ == "__main__":
    unittest.main()
