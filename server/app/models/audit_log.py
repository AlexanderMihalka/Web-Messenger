from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.types import UTCDateTime, utcnow


class AuditLog(Base):
    """Журнал ключових подій (авторизація, адмін-дії, підключення WebSocket).

    actor_id без зовнішнього ключа — щоб записи лишалися після видалення користувача.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(String(16), index=True)
    event: Mapped[str] = mapped_column(String(64), index=True)
    actor_id: Mapped[int | None] = mapped_column(default=None, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), default=None)
    message: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, server_default=func.now(), index=True
    )
