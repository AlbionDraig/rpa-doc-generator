from fastapi import Request

from app.observability import bind_logger


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
