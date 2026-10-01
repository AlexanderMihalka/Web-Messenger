"""Єдиний формат помилок API: {"error": {"code", "message", "fields?"}}."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.services.exceptions import Blocked, Conflict, Forbidden, NotFound, ServiceError


class AppError(Exception):
    status_code = 400
    code = "bad_request"
    message = "Некоректний запит"

    def __init__(
        self,
        message: str | None = None,
        *,
        fields: list[dict[str, str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
        self.fields = fields
        self.headers = headers


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    message = "Необхідна авторизація"

    def __init__(self, message: str | None = None, **kwargs: Any) -> None:
        kwargs.setdefault("headers", {"WWW-Authenticate": "Bearer"})
        super().__init__(message, **kwargs)


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"
    message = "Недостатньо прав"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "Ресурс не знайдено"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    message = "Конфлікт даних"


class PayloadTooLargeError(AppError):
    status_code = 413
    code = "payload_too_large"
    message = "Файл занадто великий"


class UnsupportedMediaError(AppError):
    status_code = 415
    code = "unsupported_media_type"
    message = "Непідтримуваний тип файлу"


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"
    message = "Забагато запитів. Спробуйте пізніше"


_HTTP_DEFAULTS: dict[int, tuple[str, str]] = {
    400: ("bad_request", "Некоректний запит"),
    401: ("unauthorized", "Необхідна авторизація"),
    403: ("forbidden", "Недостатньо прав"),
    404: ("not_found", "Ресурс не знайдено"),
    405: ("method_not_allowed", "Метод не підтримується"),
    409: ("conflict", "Конфлікт даних"),
    413: ("payload_too_large", "Запит занадто великий"),
    422: ("validation_error", "Помилка валідації даних"),
    429: ("rate_limited", "Забагато запитів. Спробуйте пізніше"),
}


def error_body(
    code: str, message: str, fields: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    body: dict[str, Any] = {"error": {"code": code, "message": message}}
    if fields:
        body["error"]["fields"] = fields
    return body


def _translate(err: dict[str, Any]) -> str:
    kind = err.get("type", "")
    ctx = err.get("ctx") or {}
    if kind == "missing":
        return "Обов'язкове поле"
    if kind == "string_too_short":
        return f"Мінімальна довжина — {ctx.get('min_length')} символів"
    if kind == "string_too_long":
        return f"Максимальна довжина — {ctx.get('max_length')} символів"
    if kind in ("string_type", "string_pattern_mismatch"):
        return "Некоректний формат тексту"
    if kind in ("int_parsing", "int_type"):
        return "Має бути цілим числом"
    if kind == "greater_than_equal":
        return f"Значення має бути не менше {ctx.get('ge')}"
    if kind == "less_than_equal":
        return f"Значення має бути не більше {ctx.get('le')}"
    if kind in ("json_invalid", "model_attributes_type", "dict_type"):
        return "Некоректний формат даних"
    if kind in ("value_error", "assertion_error"):
        return str(err.get("msg", "Некоректне значення")).removeprefix("Value error, ")
    return "Некоректне значення"


async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message, exc.fields),
        headers=dict(exc.headers or {}),
    )


async def http_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code, message = _HTTP_DEFAULTS.get(exc.status_code, ("http_error", "Помилка запиту"))
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(code, message),
        headers=dict(exc.headers or {}),
    )


async def validation_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    fields = [
        {
            "field": ".".join(str(part) for part in err["loc"][1:]) or "body",
            "message": _translate(dict(err)),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_body("validation_error", "Помилка валідації даних", fields),
    )


_SERVICE_STATUS: dict[type[ServiceError], tuple[int, str]] = {
    NotFound: (404, "not_found"),
    Conflict: (409, "conflict"),
    Forbidden: (403, "forbidden"),
    Blocked: (403, "blocked"),
}


async def service_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Перекладає винятки сервісного шару (app.services.exceptions) у HTTP-відповіді.

    Реєструється лише для базового ServiceError: Starlette сам підіймається по __mro__
    підкласу, що приходить, тож NotFound/Conflict/Forbidden/Blocked теж сюди потрапляють.
    """
    assert isinstance(exc, ServiceError)
    status_code, code = _SERVICE_STATUS.get(type(exc), (400, "bad_request"))
    return JSONResponse(status_code=status_code, content=error_body(code, str(exc)))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ServiceError, service_error_handler)
