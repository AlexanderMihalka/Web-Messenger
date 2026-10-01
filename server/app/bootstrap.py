"""Дії при старті застосунку: каталог завантажень і початковий адміністратор."""

import logging
from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import User, UserRole
from app.repositories.user_repository import UserRepository

logger = logging.getLogger("messenger.bootstrap")


def ensure_upload_dir() -> None:
    Path(settings.upload_dir, "avatars").mkdir(parents=True, exist_ok=True)


def create_default_admin() -> None:
    """Створює адміністратора з ADMIN_USERNAME/EMAIL/PASSWORD, якщо їх задано і він ще
    не існує. Ідемпотентно — безпечно викликати при кожному старті контейнера."""
    if not (settings.admin_username and settings.admin_email and settings.admin_password):
        return
    with SessionLocal() as db:
        repo = UserRepository(db)
        if repo.get_by_username(settings.admin_username) or repo.get_by_email(settings.admin_email):
            return
        admin = User(
            username=settings.admin_username.lower(),
            email=settings.admin_email.lower(),
            password_hash=hash_password(settings.admin_password),
            display_name=settings.admin_username,
            role=UserRole.ADMIN,
        )
        repo.add(admin)
        db.commit()
        logger.info("Створено початкового адміністратора username=%s", admin.username)
