from fastapi import Request

from app.limits import NoopConcurrencyLimiter
from app.observability import bind_logger


_fallback_generation_limiter = NoopConcurrencyLimiter()


def get_settings(request: Request):
    return request.app.state.settings


def get_logger(request: Request):
    request_state = getattr(request, "state", None)
    request_url = getattr(request, "url", None)
    return bind_logger(
        request.app.state.logger,
        request_id=getattr(request_state, "request_id", "-"),
        http_method=getattr(request, "method", "-"),
        http_path=getattr(request_url, "path", "-"),
    )


def get_generation_limiter(request: Request):
    app_state = getattr(getattr(request, "app", None), "state", None)
    if app_state is None:
        return _fallback_generation_limiter
    return getattr(app_state, "generation_limiter", _fallback_generation_limiter)
