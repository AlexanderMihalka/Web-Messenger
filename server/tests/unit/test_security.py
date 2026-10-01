"""Хешування паролів і JWT access-токени."""

import time

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_plaintext_and_salted() -> None:
    h1 = hash_password("Secret123")
    h2 = hash_password("Secret123")
    assert h1 != "Secret123"
    assert h1 != h2  # Argon2 використовує випадкову сіль — однакові паролі різні хеші


def test_verify_password_accepts_correct_and_rejects_wrong() -> None:
    hashed = hash_password("Secret123")
    assert verify_password("Secret123", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_handles_garbage_hash_gracefully() -> None:
    assert verify_password("Secret123", "not-a-real-hash") is False


def test_access_token_roundtrip() -> None:
    token, expires_in = create_access_token(user_id=42, role="USER")
    assert expires_in > 0
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "USER"
    assert payload["type"] == "access"


def test_decode_rejects_tampered_token() -> None:
    token, _ = create_access_token(user_id=1, role="USER")
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token + "tampered")


def test_decode_rejects_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "access_token_expire_minutes", 0)
    token, _ = create_access_token(user_id=1, role="USER")
    time.sleep(1.2)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)
