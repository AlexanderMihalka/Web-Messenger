from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Text, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.types import UTCDateTime, utcnow


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_id_id", "conversation_id", "id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
    # NULL = автора акаунта видалено адміністратором; саме повідомлення лишається в історії
    # співрозмовника (SET NULL замість CASCADE, щоб видалення користувача не стирало чужу історію).
    sender_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, default=None
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=utcnow, server_default=func.now()
    )
    # Логічне видалення: текст очищується, рядок лишається
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
