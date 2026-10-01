from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import User


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(User.username == username.lower()))

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def get_by_login(self, login: str) -> User | None:
        value = login.strip().lower()
        return self.db.scalar(select(User).where(or_(User.username == value, User.email == value)))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()

    def search(
        self, query: str, exclude_id: int, hidden_ids: set[int] | None = None, limit: int = 20
    ) -> list[User]:
        pattern = f"%{escape_like(query.strip().lower())}%"
        stmt = (
            select(User)
            .where(
                User.id != exclude_id,
                User.is_blocked.is_(False),
                or_(
                    func.lower(User.username).like(pattern, escape="\\"),
                    func.lower(User.display_name).like(pattern, escape="\\"),
                ),
            )
            .order_by(User.username)
            .limit(limit)
        )
        if hidden_ids:
            stmt = stmt.where(User.id.not_in(hidden_ids))
        return list(self.db.scalars(stmt))

    def list_public(
        self, exclude_id: int, hidden_ids: set[int], limit: int, offset: int
    ) -> tuple[list[User], int]:
        where = [User.id != exclude_id, User.is_blocked.is_(False)]
        if hidden_ids:
            where.append(User.id.not_in(hidden_ids))
        total = self.db.scalar(select(func.count()).select_from(User).where(*where)) or 0
        rows = self.db.scalars(
            select(User).where(*where).order_by(User.username).limit(limit).offset(offset)
        )
        return list(rows), total

    def list_admin(self, query: str | None, limit: int, offset: int) -> tuple[list[User], int]:
        where = []
        if query and query.strip():
            pattern = f"%{escape_like(query.strip().lower())}%"
            where.append(
                or_(
                    func.lower(User.username).like(pattern, escape="\\"),
                    func.lower(User.email).like(pattern, escape="\\"),
                    func.lower(User.display_name).like(pattern, escape="\\"),
                )
            )
        total = self.db.scalar(select(func.count()).select_from(User).where(*where)) or 0
        rows = self.db.scalars(
            select(User).where(*where).order_by(User.id).limit(limit).offset(offset)
        )
        return list(rows), total
