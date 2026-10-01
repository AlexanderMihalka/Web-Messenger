from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Conversation, Message, User, UserRole


class StatsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def user_counts(self, since_24h: datetime, since_7d: datetime) -> dict[str, int]:
        row = self.db.execute(
            select(
                func.count(User.id),
                func.count(User.id).filter(User.role == UserRole.ADMIN),
                func.count(User.id).filter(User.is_blocked.is_(True)),
                func.count(User.id).filter(User.created_at >= since_24h),
                func.count(User.id).filter(User.created_at >= since_7d),
            )
        ).one()
        return {
            "total_users": row[0],
            "admins": row[1],
            "blocked_users": row[2],
            "new_users_24h": row[3],
            "new_users_7d": row[4],
        }

    def conversation_count(self) -> int:
        return self.db.scalar(select(func.count(Conversation.id))) or 0

    def message_counts(self, since_24h: datetime) -> tuple[int, int]:
        total = self.db.scalar(select(func.count(Message.id))) or 0
        last_24h = (
            self.db.scalar(select(func.count(Message.id)).where(Message.created_at >= since_24h))
            or 0
        )
        return total, last_24h
