from fastapi import Request


def get_settings(request: Request):
    return request.app.state.settings


def get_logger(request: Request):
    return request.app.state.logger
