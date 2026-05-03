import logging


def get_request_logger() -> logging.Logger:
    return logging.getLogger("django.request")


def log_request_exception(
    message: str, raised_exception: Exception, request, *, extra: dict = None
):
    extra = {
        "request": request,
        **(extra or {}),
    }
    get_request_logger().exception(message, exc_info=raised_exception, extra=extra)
