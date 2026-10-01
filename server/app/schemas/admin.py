from datetime import datetime

from pydantic import BaseModel

from app.schemas.user import UserMe


class AdminUserOut(UserMe):
    pass


class BlockRequest(BaseModel):
    blocked: bool


class StatisticsOut(BaseModel):
    total_users: int
    admins: int
    blocked_users: int
    online_users: int
    new_users_24h: int
    new_users_7d: int
    total_conversations: int
    total_messages: int
    messages_24h: int
    websocket_connections: int


class LogOut(BaseModel):
    id: int
    level: str
    event: str
    actor_id: int | None
    ip_address: str | None
    message: str
    created_at: datetime
