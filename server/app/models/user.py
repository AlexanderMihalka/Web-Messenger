import enum
from datetime import datetime

from sqlalchemy import Boolean, Enum, String, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.types import UTCDateTime, utcnow


class UserRole(enum.StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(64), index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(255), default=None)
    bio: Mapped[str | None] = mapped_column(String(500), default=None)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=16),
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )
    # Адміністративне блокування акаунта (не плутати з таблицею Block між користувачами)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    last_seen_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, onupdate=utcnow, server_default=func.now()
    )
