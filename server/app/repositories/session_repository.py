from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models import UserSession


class SessionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, user_id: int, token_hash: str, expires_at: datetime) -> UserSession:
        session = UserSession(user_id=user_id, refresh_token_hash=token_hash, expires_at=expires_at)
        self.db.add(session)
        self.db.flush()
        return session

    def get_by_hash(self, token_hash: str) -> UserSession | None:
        return self.db.scalar(
            select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        )

    def revoke_all_for_user(self, user_id: int, now: datetime) -> None:
        self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    def purge_expired(self, user_id: int, now: datetime) -> None:
        self.db.execute(
            delete(UserSession).where(UserSession.user_id == user_id, UserSession.expires_at < now)
        )

    def delete_for_user(self, user_id: int) -> None:
        self.db.execute(delete(UserSession).where(UserSession.user_id == user_id))
