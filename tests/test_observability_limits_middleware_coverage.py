import asyncio
import logging
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.responses import Response

from app.limits import ConcurrencyLimiter, EndpointRateLimitMiddleware
from app.observability import ContextLoggerAdapter, ObservabilityMiddleware, configure_logging


class _DummyRootLogger:
    def __init__(self, handlers=None):
        self.handlers = handlers or []
        self.filter_count = 0

    def addFilter(self, _):
        self.filter_count += 1


class _DummyHandler:
    def __init__(self):
        self.filter_count = 0

    def addFilter(self, _):
        self.filter_count += 1


class _LoggerWithoutLog:
    def __init__(self):
        self.info_calls = 0
        self.error_calls = 0

    def info(self, *_args, **_kwargs):
        self.info_calls += 1

    def error(self, *_args, **_kwargs):
        self.error_calls += 1


class _LoggerWithLog:
    def __init__(self):
        self.calls = []

    def isEnabledFor(self, level):
        return level >= logging.INFO

    def log(self, level, msg, *args, **kwargs):
        self.calls.append((level, msg, args, kwargs))


class ObservabilityAndLimitsMiddlewareCoverageTests(unittest.TestCase):
    def test_context_logger_adapter_branches(self):
        logger = _LoggerWithoutLog()
        adapter = ContextLoggerAdapter(logger, {"base": "x"})

        adapter.process("msg", {"extra": {"custom": "y"}})
        adapter.process("msg", {"extra": [("list_key", "value")]})
        self.assertTrue(adapter.isEnabledFor(logging.INFO))
        adapter.log(logging.INFO, "hello %s", "world")
        adapter.exception("boom")

        self.assertGreaterEqual(logger.info_calls, 1)
        self.assertGreaterEqual(logger.error_calls, 1)

        logger_with_log = _LoggerWithLog()
        adapter_with_log = ContextLoggerAdapter(logger_with_log, {"k": "v"})
        self.assertTrue(adapter_with_log.isEnabledFor(logging.INFO))
        adapter_with_log.log(logging.INFO, "ok")
        self.assertTrue(logger_with_log.calls)

    def test_configure_logging_no_handlers_and_handlers(self):
        settings = SimpleNamespace(app_log_level="info")
        no_handler_logger = _DummyRootLogger(handlers=[])

        with patch("app.observability.logging.getLogger", return_value=no_handler_logger):
            configure_logging(settings)
        self.assertEqual(no_handler_logger.filter_count, 1)

        handler = _DummyHandler()
        has_handlers_logger = _DummyRootLogger(handlers=[handler])
        with patch("app.observability.logging.getLogger", return_value=has_handlers_logger):
            configure_logging(settings)
        self.assertEqual(handler.filter_count, 1)

    def test_observability_middleware_success_and_error(self):
        middleware = ObservabilityMiddleware(app=None, logger=logging.getLogger("test.obs"))

        request = SimpleNamespace(
            headers={"X-Request-ID": "req-abc"},
            state=SimpleNamespace(),
            method="GET",
            url=SimpleNamespace(path="/ok"),
        )

        async def success_call_next(_request):
            return Response(content="ok", status_code=200)

        response = asyncio.run(middleware.dispatch(request, success_call_next))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Request-ID"), "req-abc")
        self.assertEqual(request.state.request_id, "req-abc")

        error_request = SimpleNamespace(
            headers={},
            state=SimpleNamespace(),
            method="GET",
            url=SimpleNamespace(path="/boom"),
        )

        async def failing_call_next(_request):
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            asyncio.run(middleware.dispatch(error_request, failing_call_next))

    def test_endpoint_rate_limit_middleware_branches(self):
        middleware = EndpointRateLimitMiddleware(
            app=None,
            logger=logging.getLogger("test.rate"),
            enabled=True,
            limit=1,
            window_seconds=60,
            protected_paths={"/protected"},
        )

        open_request = SimpleNamespace(
            url=SimpleNamespace(path="/open"),
            client=SimpleNamespace(host="127.0.0.1"),
            state=SimpleNamespace(request_id="rid-open"),
            method="GET",
        )

        protected_request = SimpleNamespace(
            url=SimpleNamespace(path="/protected"),
            client=SimpleNamespace(host="127.0.0.1"),
            state=SimpleNamespace(request_id="rid-1"),
            method="GET",
        )

        async def next_response(_request):
            return Response(content="ok", status_code=200)

        open_response = asyncio.run(middleware.dispatch(open_request, next_response))
        self.assertEqual(open_response.status_code, 200)

        allowed = asyncio.run(middleware.dispatch(protected_request, next_response))
        self.assertEqual(allowed.status_code, 200)
        self.assertIn("X-RateLimit-Remaining", allowed.headers)

        blocked = asyncio.run(middleware.dispatch(protected_request, next_response))
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("rate_limit_exceeded", blocked.body.decode("utf-8"))
        self.assertIn("Retry-After", blocked.headers)

        unknown_host_request = SimpleNamespace(
            url=SimpleNamespace(path="/protected"),
            client=None,
            state=SimpleNamespace(request_id="rid-unknown"),
            method="GET",
        )

        # separate middleware instance to avoid shared counters from earlier requests
        middleware_unknown = EndpointRateLimitMiddleware(
            app=None,
            logger=logging.getLogger("test.rate.unknown"),
            enabled=True,
            limit=1,
            window_seconds=60,
            protected_paths={"/protected"},
        )
        response_unknown = asyncio.run(middleware_unknown.dispatch(unknown_host_request, next_response))
        self.assertEqual(response_unknown.status_code, 200)

        disabled_middleware = EndpointRateLimitMiddleware(
            app=None,
            logger=logging.getLogger("test.rate.disabled"),
            enabled=False,
            limit=1,
            window_seconds=60,
            protected_paths={"/protected"},
        )

        first = asyncio.run(disabled_middleware.dispatch(protected_request, next_response))
        second = asyncio.run(disabled_middleware.dispatch(protected_request, next_response))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

    def test_concurrency_limiter_zero_timeout_branch(self):
        async def scenario():
            limiter = ConcurrencyLimiter(limit=1, acquire_timeout_seconds=0)
            async with limiter.slot() as acquired:
                self.assertTrue(acquired)

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
