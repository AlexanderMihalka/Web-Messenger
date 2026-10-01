from datetime import datetime

from pydantic import BaseModel

from app.schemas.message import MessageOut
from app.schemas.user import UserPublic


class ConversationCreate(BaseModel):
    user_id: int


class ConversationOut(BaseModel):
    id: int
    partner: UserPublic
    last_message: MessageOut | None = None
    unread_count: int
    updated_at: datetime
    blocked_by_me: bool
    can_send: bool
