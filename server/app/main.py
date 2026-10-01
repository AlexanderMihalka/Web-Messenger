"""Точка входу FastAPI-застосунку Messenger Web."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.bootstrap import create_default_admin, ensure_upload_dir
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import ErrorLoggingMiddleware, GeneralRateLimitMiddleware
from app.routers import admin, auth, conversations, messages, users
from app.websocket.chat import router as websocket_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.log_level)
    ensure_upload_dir()
    create_default_admin()
    yield


app = FastAPI(title=settings.app_name, version="1.1.0", lifespan=lifespan)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(admin.router)
app.include_router(websocket_router)

# check_dir=False: каталог створюється в lifespan (ще не існує в момент імпорту модуля).
app.mount("/uploads", StaticFiles(directory=settings.upload_dir, check_dir=False), name="uploads")


@app.get("/api/v1/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# Порядок важливий: останній доданий middleware стає зовнішнім і бачить усі відповіді,
# включно з 429 від rate-limit і 500 від ErrorLoggingMiddleware — тому CORS додається останнім.
app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(GeneralRateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
