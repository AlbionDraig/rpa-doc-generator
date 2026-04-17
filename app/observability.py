import logging
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware

_request_id_var = ContextVar("request_id", default="-")
_session_id_var = ContextVar("session_id", default="-")


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(record, "request_id", _request_id_var.get())
        record.session_id = getattr(record, "session_id", _session_id_var.get())
        record.http_method = getattr(record, "http_method", "-")
        record.http_path = getattr(record, "http_path", "-")
        return True


class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        base_extra = self.extra if self.extra is not None else {}
        extra = dict(base_extra)

        incoming_extra = kwargs.get("extra")
        if isinstance(incoming_extra, dict):
            extra.update(incoming_extra)
        elif incoming_extra is not None:
            extra.update(dict(incoming_extra))

        kwargs["extra"] = extra
        return msg, kwargs

    def isEnabledFor(self, level):
        checker = getattr(self.logger, "isEnabledFor", None)
        if checker is None:
            return True
        return checker(level)

    def log(self, level, msg, *args, **kwargs):
        msg, kwargs = self.process(msg, kwargs)
        if hasattr(self.logger, "log"):
            return self.logger.log(level, msg, *args, **kwargs)

        level_name = logging.getLevelName(level).lower()
        target = getattr(self.logger, level_name, None) or getattr(self.logger, "info", None)
        if target is not None:
            return target(msg, *args, **kwargs)
        return None

    def exception(self, msg, *args, exc_info=True, **kwargs):
        kwargs["exc_info"] = exc_info
        return self.log(logging.ERROR, msg, *args, **kwargs)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        token = _request_id_var.set(request_id)
        started_at = time.perf_counter()

        request_logger = bind_logger(
            self.logger,
            request_id=request_id,
            http_method=request.method,
            http_path=request.url.path,
        )
        request_logger.info("HTTP request started")

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            request_logger.exception("HTTP request failed in %sms", duration_ms)
            raise
        finally:
            _request_id_var.reset(token)

        response.headers["X-Request-ID"] = request_id
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        request_logger.info(
            "HTTP request completed in %sms with status %s",
            duration_ms,
            getattr(response, "status_code", "unknown"),
        )
        return response


def configure_logging(settings):
    logging.basicConfig(
        level=getattr(logging, settings.app_log_level.upper(), logging.INFO),
        format=(
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[request_id=%(request_id)s session_id=%(session_id)s] %(message)s"
        ),
    )

    context_filter = RequestContextFilter()
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.addFilter(context_filter)
        return

    for handler in root_logger.handlers:
        handler.addFilter(context_filter)


def bind_logger(logger, **context):
    return ContextLoggerAdapter(logger, context)


def bind_session(session_id):
    return _session_id_var.set(session_id)


def reset_session(token):
    _session_id_var.reset(token)
