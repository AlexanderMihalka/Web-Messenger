"""Адміністративні операції: користувачі, блокування, статистика, журнали."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.repositories.audit_repository import AuditRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.stats_repository import StatsRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import AdminUserOut, LogOut, StatisticsOut
from app.schemas.common import Page
from app.services import audit
from app.services.exceptions import Conflict, Forbidden, NotFound
from app.services.mappers import to_user_me
from app.websocket.manager import manager


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.sessions = SessionRepository(db)
        self.stats = StatsRepository(db)
        self.logs = AuditRepository(db)

    def list_users(self, query: str | None, limit: int, offset: int) -> Page[AdminUserOut]:
        rows, total = self.users.list_admin(query, limit, offset)
        return Page(
            items=[AdminUserOut(**to_user_me(u).model_dump()) for u in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def set_blocked(self, actor: User, target_id: int, blocked: bool) -> AdminUserOut:
        target = self.users.get(target_id)
        if target is None:
            raise NotFound("Користувача не знайдено")
        if target.id == actor.id:
            raise Conflict("Не можна заблокувати власний обліковий запис")
        if target.role == UserRole.ADMIN:
            raise Forbidden("Не можна блокувати інших адміністраторів")
        target.is_blocked = blocked
        if blocked:
            self.sessions.revoke_all_for_user(target.id, datetime.now(UTC))
        audit.record(
            self.db,
            event="admin_block" if blocked else "admin_unblock",
            actor_id=actor.id,
            message=f"target_id={target.id}",
        )
        self.db.commit()
        self.db.refresh(target)
        return AdminUserOut(**to_user_me(target).model_dump())

    def delete_user(self, actor: User, target_id: int) -> None:
        target = self.users.get(target_id)
        if target is None:
            raise NotFound("Користувача не знайдено")
        if target.id == actor.id:
            raise Conflict("Не можна видалити власний обліковий запис")
        if target.role == UserRole.ADMIN:
            raise Forbidden("Не можна видаляти інших адміністраторів")
        self.users.delete(target)
        audit.record(
            self.db, event="admin_delete_user", actor_id=actor.id, message=f"target_id={target_id}"
        )
        self.db.commit()

    def statistics(self) -> StatisticsOut:
        now = datetime.now(UTC)
        counts = self.stats.user_counts(now - timedelta(hours=24), now - timedelta(days=7))
        total_messages, messages_24h = self.stats.message_counts(now - timedelta(hours=24))
        return StatisticsOut(
            **counts,
            online_users=manager.online_user_count(),
            total_conversations=self.stats.conversation_count(),
            total_messages=total_messages,
            messages_24h=messages_24h,
            websocket_connections=manager.connection_count(),
        )

    def get_logs(
        self, level: str | None, event: str | None, limit: int, offset: int
    ) -> Page[LogOut]:
        rows, total = self.logs.list(level, event, limit, offset)
        items = [LogOut.model_validate(r, from_attributes=True) for r in rows]
        return Page(items=items, total=total, limit=limit, offset=offset)
