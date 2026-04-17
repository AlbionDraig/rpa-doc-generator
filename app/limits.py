import asyncio
import time
from collections import deque
from contextlib import asynccontextmanager

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability import bind_logger


class ConcurrencyLimiter:
    def __init__(self, limit, acquire_timeout_seconds):
        self._limit = max(1, int(limit or 1))
        self._acquire_timeout_seconds = max(0.0, float(acquire_timeout_seconds or 0))
        self._semaphore = asyncio.Semaphore(self._limit)

    @asynccontextmanager
    async def slot(self):
        acquired = False
        try:
            if self._acquire_timeout_seconds == 0:
                await self._semaphore.acquire()
                acquired = True
            else:
                await asyncio.wait_for(self._semaphore.acquire(), timeout=self._acquire_timeout_seconds)
                acquired = True
        except TimeoutError:
            acquired = False

        try:
            yield acquired
        finally:
            if acquired:
                self._semaphore.release()


class NoopConcurrencyLimiter:
    @asynccontextmanager
    async def slot(self):
        yield True


class SlidingWindowRateLimiter:
    def __init__(self, limit, window_seconds):
        self._limit = max(1, int(limit or 1))
        self._window_seconds = max(1, int(window_seconds or 1))
        self._events_by_key = {}

    def check(self, key, now=None):
        current_time = float(time.monotonic() if now is None else now)
        events = self._events_by_key.setdefault(key, deque())
        cutoff = current_time - self._window_seconds

        while events and events[0] <= cutoff:
            events.popleft()

        if len(events) >= self._limit:
            retry_after = max(1, int(self._window_seconds - (current_time - events[0])))
            return False, retry_after, 0

        events.append(current_time)
        remaining = max(0, self._limit - len(events))
        return True, 0, remaining


class EndpointRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        logger,
        enabled,
        limit,
        window_seconds,
        protected_paths,
    ):
        super().__init__(app)
        self._logger = logger
        self._enabled = bool(enabled)
        self._protected_paths = set(protected_paths or [])
        self._limiter = SlidingWindowRateLimiter(limit=limit, window_seconds=window_seconds)

    async def dispatch(self, request, call_next):
        if not self._enabled or request.url.path not in self._protected_paths:
            return await call_next(request)

        client_host = getattr(getattr(request, "client", None), "host", "unknown")
        key = f"{client_host}:{request.url.path}"
        allowed, retry_after, remaining = self._limiter.check(key)

        if not allowed:
            logger = bind_logger(
                self._logger,
                request_id=getattr(request.state, "request_id", "-"),
                http_method=request.method,
                http_path=request.url.path,
            )
            logger.warning("Rate limit exceeded for key=%s retry_after=%s", key, retry_after)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": {
                        "error": "Demasiadas solicitudes. Intenta nuevamente en unos segundos.",
                        "code": "rate_limit_exceeded",
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Remaining": str(remaining),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
