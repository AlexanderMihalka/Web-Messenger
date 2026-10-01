from datetime import datetime

from pydantic import BaseModel, field_validator

from app.schemas import validators as v


class MessageCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def _content(cls, value: str) -> str:
        return v.check_message(value)


class MessageUpdate(MessageCreate):
    pass


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int | None  # None = акаунт автора видалено адміністратором
    content: str
    created_at: datetime
    updated_at: datetime
    is_edited: bool
    is_deleted: bool
    is_read: bool


class MessagePage(BaseModel):
    items: list[MessageOut]
    has_more: bool


class ReadResult(BaseModel):
    conversation_id: int
    last_read_message_id: int
    unread_count: int
