"""WebSocket-ендпоінт: /ws?token=<access_token> — одне зʼєднання на користувача (ТЗ п.12,
уточнення: не одне з'єднання на діалог, бо тоді список чатів не оновлював би presence/typing
для згорнутих діалогів). Токен передається як query-параметр, оскільки браузерний WebSocket
API не дозволяє додати заголовок Authorization під час рукостискання.
"""

import json
import logging
from datetime import UTC, datetime

from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.core.database import SessionLocal
from app.core.security import InvalidTokenError, decode_access_token
from app.models import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.websocket import events
from app.websocket.manager import manager

logger = logging.getLogger("messenger.ws")
audit_log = logging.getLogger("messenger.audit")
router = APIRouter()

CLOSE_UNAUTHORIZED = 4401


def _authenticate(token: str | None) -> User | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (InvalidTokenError, ValueError, KeyError):
        return None
    with SessionLocal() as db:
        user = UserRepository(db).get(user_id)
        if user is None or user.is_blocked:
            return None
        db.expunge(user)
        return user


def _partner_ids(user_id: int) -> set[int]:
    with SessionLocal() as db:
        return set(ConversationRepository(db).partner_ids(user_id))


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    user = _authenticate(token)
    if user is None:
        await websocket.close(code=CLOSE_UNAUTHORIZED, reason="unauthorized")
        return

    await websocket.accept()
    became_online = await manager.connect(user.id, websocket)
    audit_log.info("ws_connect user_id=%s", user.id)
    await websocket.send_json(
        {"type": "connection", "user_id": user.id, "server_time": datetime.now(UTC).isoformat()}
    )

    if became_online:
        partner_ids = _partner_ids(user.id)
        if partner_ids:
            await manager.send_to_users(partner_ids, events.user_online(user.id))

    try:
        while True:
            raw = await websocket.receive_text()
            await _handle_client_event(user, raw)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("ws_error user_id=%s", user.id)
    finally:
        became_offline = await manager.disconnect(user.id, websocket)
        if became_offline:
            now = datetime.now(UTC)
            with SessionLocal() as db:
                repo = UserRepository(db)
                db_user = repo.get(user.id)
                if db_user is not None:
                    db_user.last_seen_at = now
                    db.commit()
            audit_log.info("ws_disconnect user_id=%s", user.id)
            partner_ids = _partner_ids(user.id)
            if partner_ids:
                await manager.send_to_users(partner_ids, events.user_offline(user.id, now))


async def _handle_client_event(user: User, raw: str) -> None:
    try:
        data = json.loads(raw)
        event_type = data.get("type") if isinstance(data, dict) else None
    except json.JSONDecodeError:
        await manager.send_to_user(user.id, {"type": "error", "message": "Некоректний формат повідомлення"})
        return

    if event_type == "ping":
        await manager.send_to_user(user.id, {"type": "pong"})
        return

    if event_type in ("typing:start", "typing:stop"):
        conversation_id = data.get("conversation_id")
        if not isinstance(conversation_id, int):
            return
        with SessionLocal() as db:
            repo = ConversationRepository(db)
            if repo.get_member(conversation_id, user.id) is None:
                return
            other_ids = [m.user_id for m in repo.get_members(conversation_id) if m.user_id != user.id]
        for other_id in other_ids:
            await manager.send_to_user(other_id, events.typing(event_type, conversation_id, user.id))
        return

    await manager.send_to_user(
        user.id, {"type": "error", "message": f"Невідомий тип події: {event_type}"}
    )
