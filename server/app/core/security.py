"""Паролі (Argon2id), JWT access-токени та refresh-токени."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import settings

_hasher = PasswordHasher()  # Argon2id з рекомендованими параметрами
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")

InvalidTokenError = jwt.PyJWTError


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def verify_dummy(password: str) -> None:
    """Вирівнює час відповіді, коли користувача не знайдено (захист від user enumeration)."""
    verify_password(password, _DUMMY_HASH)


def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    """Повертає (токен, час життя в секундах)."""
    now = datetime.now(UTC)
    expires_in = settings.access_token_expire_minutes * 60
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm), expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """Перевіряє підпис і термін дії. Кидає InvalidTokenError (jwt.PyJWTError)."""
    payload: dict[str, Any] = jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    if payload.get("type") != "access" or "sub" not in payload:
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """У БД зберігається лише SHA-256 від refresh-токена."""
    return hashlib.sha256(token.encode()).hexdigest()
