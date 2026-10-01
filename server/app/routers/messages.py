"""/api/v1/conversations/{id}/messages, /api/v1/messages/{id} — REST-канал повідомлень.

REST лишається єдиним джерелом істини для збереження в PostgreSQL (ТЗ п.12): POST створює
рядок у БД і повертає його; WebSocket використовується тільки для розсилки вже збереженої
події іншим підключеним учасникам. Власна вкладка відправника отримає той самий message:new
по сокету, що і REST-відповідь — клієнт звіряє за id і не дублює повідомлення в UI.
"""

import anyio
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.message import MessageCreate, MessageOut, MessagePage, MessageUpdate, ReadResult
from app.services.message_service import MessageService
from app.websocket import events
from app.websocket.manager import manager

router = APIRouter(prefix="/api/v1", tags=["messages"])


def _member_ids(db: Session, conversation_id: int) -> list[int]:
    return [m.user_id for m in ConversationRepository(db).get_members(conversation_id)]


@router.get("/conversations/{conversation_id}/messages", response_model=MessagePage)
def list_messages(
    conversation_id: int,
    after_id: int = Query(
        0, ge=0, description="Наздогнати пропущене: наступні повідомлення після цього id (без before_id)"
    ),
    before_id: int | None = Query(
        None, ge=1, description="Гортання вгору: попередня сторінка, старіша за це id"
    ),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessagePage:
    return MessageService(db).list_page(user, conversation_id, after_id, before_id, limit)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut, status_code=201)
def send_message(
    conversation_id: int,
    data: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageOut:
    out = MessageService(db).send(user, conversation_id, data.content)
    recipients = _member_ids(db, conversation_id)
    anyio.from_thread.run(manager.send_to_users, recipients, events.message_new(out))
    return out


@router.patch("/messages/{message_id}", response_model=MessageOut)
def edit_message(
    message_id: int,
    data: MessageUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageOut:
    out = MessageService(db).edit(user, message_id, data.content)
    recipients = _member_ids(db, out.conversation_id)
    anyio.from_thread.run(manager.send_to_users, recipients, events.message_edit(out))
    return out


@router.delete("/messages/{message_id}", response_model=MessageOut)
def delete_message(
    message_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MessageOut:
    out = MessageService(db).delete(user, message_id)
    recipients = _member_ids(db, out.conversation_id)
    anyio.from_thread.run(manager.send_to_users, recipients, events.message_delete(out))
    return out


@router.post("/messages/{message_id}/read", response_model=ReadResult)
def read_message(
    message_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ReadResult:
    result = MessageService(db).mark_read(user, message_id)
    recipients = _member_ids(db, result.conversation_id)
    payload = events.message_read(result.conversation_id, user.id, result.last_read_message_id)
    anyio.from_thread.run(manager.send_to_users, recipients, payload)
    return result
