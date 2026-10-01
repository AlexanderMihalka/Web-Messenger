"""Фабрики WebSocket-подій — єдине місце, де формується форма кожного типу події.

Повідомлення передаються вже серіалізованим MessageOut (сервісний шар порахував
is_read у read-receipt-семантиці, однаковій для обох учасників — див. mappers.to_message_out).
"""

from datetime import datetime

from app.schemas.message import MessageOut


def user_online(user_id: int) -> dict:
    return {"type": "user:online", "user_id": user_id}


def user_offline(user_id: int, last_seen_at: datetime) -> dict:
    return {"type": "user:offline", "user_id": user_id, "last_seen_at": last_seen_at.isoformat()}


def message_new(message: MessageOut) -> dict:
    return {
        "type": "message:new",
        "conversation_id": message.conversation_id,
        "message": message.model_dump(mode="json"),
    }


def message_edit(message: MessageOut) -> dict:
    return {
        "type": "message:edit",
        "conversation_id": message.conversation_id,
        "message": message.model_dump(mode="json"),
    }


def message_delete(message: MessageOut) -> dict:
    return {
        "type": "message:delete",
        "conversation_id": message.conversation_id,
        "message_id": message.id,
    }


def message_read(conversation_id: int, user_id: int, last_read_message_id: int) -> dict:
    return {
        "type": "message:read",
        "conversation_id": conversation_id,
        "user_id": user_id,
        "last_read_message_id": last_read_message_id,
    }


def typing(event_type: str, conversation_id: int, user_id: int) -> dict:
    return {"type": event_type, "conversation_id": conversation_id, "user_id": user_id}
