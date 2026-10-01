"""ASGI middleware: загальний rate limit (по IP) + ідентифікатор запиту в логах помилок 500."""

import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.errors import error_body
from app.core.rate_limit import client_ip, limiter

logger = logging.getLogger("messenger.request")


class GeneralRateLimitMiddleware(BaseHTTPMiddleware):
    """Груба перевірка по IP на весь /api/v1/*. Специфічні ендпоінти (auth) мають власний,
    суворіший ліміт через Depends(rate_limit(...))."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if settings.rate_limit_enabled and request.url.path.startswith("/api/"):
            allowed, retry_after = limiter.check(
                f"general:{client_ip(request)}", settings.rate_limit_general_per_minute, 60
            )
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content=error_body("rate_limited", "Забагато запитів. Спробуйте пізніше"),
                    headers={"Retry-After": str(retry_after)},
                )
        return await call_next(request)


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Присвоює кожному запиту request_id і логує необроблені винятки як 500,
    щоб вони не губилися серед звичайних логів доступу."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled_error request_id=%s path=%s", request_id, request.url.path)
            return JSONResponse(
                status_code=500,
                content=error_body("internal_error", "Внутрішня помилка сервера"),
            )
        response.headers["X-Request-ID"] = request_id
        return response
