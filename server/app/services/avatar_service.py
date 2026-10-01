"""Завантаження та нормалізація аватарів користувачів."""

import io
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.core.errors import PayloadTooLargeError, UnsupportedMediaError

MAX_DIMENSION = 512
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


def save_avatar(user_id: int, raw_bytes: bytes) -> str:
    """Не довіряє Content-Type від клієнта: перевіряє байти через Pillow, масштабує
    до розумного розміру та перезаписує як PNG. Повертає публічний URL файлу."""
    if len(raw_bytes) > settings.max_avatar_bytes:
        raise PayloadTooLargeError(
            f"Максимальний розмір файлу — {settings.max_avatar_bytes // (1024 * 1024)} МБ"
        )
    try:
        probe = Image.open(io.BytesIO(raw_bytes))
        probe.verify()  # перевірка цілісності файлу
        opened = Image.open(io.BytesIO(raw_bytes))  # verify() «зʼїдає» дескриптор — відкриваємо знову
        if opened.format not in ALLOWED_FORMATS:
            raise UnsupportedMediaError("Підтримуються лише JPEG, PNG, WEBP, GIF")
        image: Image.Image = opened.convert("RGBA")
    except (UnidentifiedImageError, OSError) as exc:
        raise UnsupportedMediaError("Файл не є дійсним зображенням") from exc

    image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
    directory = Path(settings.upload_dir) / "avatars" / str(user_id)
    directory.mkdir(parents=True, exist_ok=True)
    for old in directory.glob("*.png"):  # прибираємо попередній аватар, щоб диск не смітився
        old.unlink(missing_ok=True)
    filename = f"{uuid.uuid4().hex}.png"
    image.save(directory / filename, format="PNG")
    return f"/uploads/avatars/{user_id}/{filename}"
