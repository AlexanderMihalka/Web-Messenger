from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self, level: str | None, event: str | None, limit: int, offset: int
    ) -> tuple[list[AuditLog], int]:
        where = []
        if level:
            where.append(AuditLog.level == level.upper())
        if event:
            where.append(AuditLog.event.like(f"{event}%"))
        total = self.db.scalar(select(func.count()).select_from(AuditLog).where(*where)) or 0
        rows = self.db.scalars(
            select(AuditLog)
            .where(*where)
            .order_by(AuditLog.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(rows), total
