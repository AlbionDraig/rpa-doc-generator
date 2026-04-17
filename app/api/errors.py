from fastapi import HTTPException


def build_http_error(status_code: int, message: str, code: str):
    return HTTPException(
        status_code=status_code,
        detail={
            "error": message,
            "code": code,
        },
    )


def map_exception_to_http(exc: Exception, logger, prefix: str = ""):
    context = f"{prefix}: " if prefix else ""

    if isinstance(exc, ValueError):
        logger.error("[ERROR] %sValidacion: %s", context, exc)
        return build_http_error(400, f"Error de validacion: {exc}", "validation_error")

    if isinstance(exc, FileNotFoundError):
        logger.error("[ERROR] %sArchivo no encontrado: %s", context, exc)
        return build_http_error(404, f"No encontrado: {exc}", "not_found")

    logger.error("[ERROR] %sInesperado: %s", context, exc, exc_info=True)
    return build_http_error(500, "Error interno del servidor", "internal_error")
