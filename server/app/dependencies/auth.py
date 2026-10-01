"""Перевірка access-токена (Bearer) для захищених REST-маршрутів."""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import InvalidTokenError, decode_access_token
from app.models import User
from app.repositories.user_repository import UserRepository


def extract_bearer_token(request: Request) -> str | None:
    header = request.headers.get("Authorization")
    if not header:
        return None
    scheme, _, param = header.partition(" ")
    if scheme.lower() != "bearer" or not param:
        return None
    return param


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = extract_bearer_token(request)
    if token is None:
        raise UnauthorizedError("Необхідна авторизація")
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (InvalidTokenError, ValueError, KeyError) as exc:
        raise UnauthorizedError("Недійсний або прострочений токен") from exc
    user = UserRepository(db).get(user_id)
    if user is None:
        raise UnauthorizedError("Користувача не знайдено")
    if user.is_blocked:
        raise ForbiddenError("Обліковий запис заблоковано адміністратором")
    return user
