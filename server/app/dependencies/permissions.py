"""Перевірка ролі ADMIN для адміністративних маршрутів."""

from fastapi import Depends

from app.core.errors import ForbiddenError
from app.dependencies.auth import get_current_user
from app.models import User, UserRole


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Потрібні права адміністратора")
    return user
