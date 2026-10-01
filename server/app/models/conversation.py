from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.types import UTCDateTime, utcnow


class Conversation(Base):
    """Приватний діалог двох користувачів. direct_key = "<менший id>:<більший id>" (унікальний)."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    direct_key: Mapped[str] = mapped_column(String(32), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, server_default=func.now()
    )


class ConversationMember(Base):
    __tablename__ = "conversation_members"
    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_conversation_members_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    joined_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, server_default=func.now()
    )
    # «Курсор прочитаного» — id останнього повідомлення, яке учасник уже прочитав.
    # Надійніший за last_read_at (немає колізій з однаковим часом/розсинхроном годинника).
    last_read_message_id: Mapped[int] = mapped_column(default=0, server_default="0")
    last_read_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    # «Приховати для мене» — діалог зникає зі списку, доки не прийде нове повідомлення.
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
