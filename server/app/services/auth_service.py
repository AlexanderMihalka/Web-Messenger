"""Реєстрація, вхід, оновлення токенів, вихід."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_dummy,
    verify_password,
)
from app.models import User, UserRole
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest
from app.services import audit
from app.services.exceptions import Conflict, Forbidden, NotFound


class AuthResult:
    def __init__(self, user: User, access_token: str, expires_in: int, refresh_token: str) -> None:
        self.user = user
        self.access_token = access_token
        self.expires_in = expires_in
        self.refresh_token = refresh_token


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.sessions = SessionRepository(db)

    def register(self, data: RegisterRequest, *, ip: str) -> AuthResult:
        if self.users.get_by_username(data.username):
            raise Conflict("Це імʼя користувача вже зайняте")
        if self.users.get_by_email(data.email):
            raise Conflict("Ця електронна адреса вже зареєстрована")

        user = User(
            username=data.username.lower(),
            email=data.email,
            password_hash=hash_password(data.password),
            display_name=data.display_name or data.username,
            role=UserRole.USER,
        )
        self.users.add(user)
        audit.record(self.db, event="register", actor_id=user.id, ip_address=ip, message=user.username)
        self.db.commit()
        return self._issue_tokens(user)

    def login(self, login: str, password: str, *, ip: str) -> AuthResult:
        user = self.users.get_by_login(login)
        if user is None:
            verify_dummy(password)  # без цього час відповіді видає, що юзера не існує
            audit.record(
                self.db, event="login_failed", level="WARNING", ip_address=ip,
                message=f"login={login!r} reason=not_found",
            )
            self.db.commit()
            raise NotFound("Невірний логін або пароль")
        if not verify_password(password, user.password_hash):
            audit.record(
                self.db, event="login_failed", level="WARNING", actor_id=user.id, ip_address=ip,
                message="reason=bad_password",
            )
            self.db.commit()
            raise NotFound("Невірний логін або пароль")
        if user.is_blocked:
            audit.record(
                self.db, event="login_blocked", level="WARNING", actor_id=user.id, ip_address=ip
            )
            self.db.commit()
            raise Forbidden("Обліковий запис заблоковано адміністратором")
        audit.record(self.db, event="login", actor_id=user.id, ip_address=ip)
        self.db.commit()
        return self._issue_tokens(user)

    def refresh(self, raw_token: str, *, ip: str) -> AuthResult:
        token_hash = hash_refresh_token(raw_token)
        session = self.sessions.get_by_hash(token_hash)
        now = datetime.now(UTC)
        if session is None or session.revoked_at is not None or session.expires_at < now:
            audit.record(self.db, event="refresh_failed", level="WARNING", ip_address=ip)
            self.db.commit()
            raise NotFound("Сесію завершено. Увійдіть повторно")
        user = self.users.get(session.user_id)
        if user is None or user.is_blocked:
            raise Forbidden("Обліковий запис недоступний")
        # Ротація: старий refresh-токен одразу анулюємо, видаємо новий
        session.revoked_at = now
        self.db.flush()
        return self._issue_tokens(user)

    def logout(self, raw_token: str | None, user_id: int) -> None:
        if raw_token:
            session = self.sessions.get_by_hash(hash_refresh_token(raw_token))
            if session and session.user_id == user_id:
                session.revoked_at = datetime.now(UTC)
        audit.record(self.db, event="logout", actor_id=user_id)
        self.db.commit()

    def _issue_tokens(self, user: User) -> AuthResult:
        access_token, expires_in = create_access_token(user.id, user.role.value)
        raw_refresh = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
        self.sessions.purge_expired(user.id, datetime.now(UTC))
        self.sessions.add(user.id, hash_refresh_token(raw_refresh), expires_at)
        self.db.commit()
        return AuthResult(user, access_token, expires_in, raw_refresh)
