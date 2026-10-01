"""AuthService: реєстрація, вхід, оновлення та ротація refresh-токена, вихід."""

import pytest
from sqlalchemy.orm import Session

from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService
from app.services.exceptions import Conflict, Forbidden, NotFound
from tests.conftest import make_user


def _register(db: Session, **overrides: object) -> RegisterRequest:
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "Secret123",
        "confirm_password": "Secret123",
        "display_name": "New User",
    }
    data.update(overrides)
    return RegisterRequest(**data)  # type: ignore[arg-type]


def test_register_creates_user_and_tokens(db: Session) -> None:
    service = AuthService(db)
    result = service.register(_register(db), ip="127.0.0.1")
    assert result.user.username == "newuser"
    assert result.access_token
    assert result.refresh_token
    assert result.expires_in > 0


def test_register_rejects_duplicate_username(db: Session) -> None:
    make_user(db, username="taken")
    service = AuthService(db)
    with pytest.raises(Conflict):
        service.register(_register(db, username="taken", email="other@example.com"), ip="127.0.0.1")


def test_register_rejects_duplicate_email(db: Session) -> None:
    make_user(db, username="someone", email="dup@example.com")
    service = AuthService(db)
    with pytest.raises(Conflict):
        service.register(_register(db, username="another", email="dup@example.com"), ip="127.0.0.1")


def test_login_succeeds_with_username_or_email(db: Session) -> None:
    make_user(db, username="bob", email="bob@example.com", password="Secret123")
    service = AuthService(db)
    assert service.login("bob", "Secret123", ip="127.0.0.1").user.username == "bob"
    assert service.login("bob@example.com", "Secret123", ip="127.0.0.1").user.username == "bob"


def test_login_rejects_wrong_password(db: Session) -> None:
    make_user(db, username="bob", password="Secret123")
    with pytest.raises(NotFound):
        AuthService(db).login("bob", "WrongPass1", ip="127.0.0.1")


def test_login_rejects_unknown_user(db: Session) -> None:
    with pytest.raises(NotFound):
        AuthService(db).login("ghost", "Secret123", ip="127.0.0.1")


def test_login_rejects_blocked_user(db: Session) -> None:
    user = make_user(db, username="blocked", password="Secret123")
    user.is_blocked = True
    db.commit()
    with pytest.raises(Forbidden):
        AuthService(db).login("blocked", "Secret123", ip="127.0.0.1")


def test_refresh_rotates_token_and_invalidates_old_one(db: Session) -> None:
    make_user(db, username="carol", password="Secret123")
    service = AuthService(db)
    first = service.login("carol", "Secret123", ip="127.0.0.1")

    second = service.refresh(first.refresh_token, ip="127.0.0.1")
    assert second.refresh_token != first.refresh_token

    with pytest.raises(NotFound):
        service.refresh(first.refresh_token, ip="127.0.0.1")  # старий токен вже відкликано


def test_refresh_rejects_unknown_token(db: Session) -> None:
    with pytest.raises(NotFound):
        AuthService(db).refresh("not-a-real-token", ip="127.0.0.1")


def test_logout_revokes_session_so_refresh_fails_after(db: Session) -> None:
    make_user(db, username="dave", password="Secret123")
    service = AuthService(db)
    result = service.login("dave", "Secret123", ip="127.0.0.1")
    service.logout(result.refresh_token, result.user.id)
    with pytest.raises(NotFound):
        service.refresh(result.refresh_token, ip="127.0.0.1")
