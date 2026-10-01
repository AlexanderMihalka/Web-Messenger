"""/api/v1/conversations — список, створення, перегляд, приховання приватних діалогів."""

import anyio
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.conversation import ConversationCreate, ConversationOut
from app.services.conversation_service import ConversationService
from app.websocket import events
from app.websocket.manager import manager

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ConversationOut]:
    return ConversationService(db).list_for_user(user)


@router.post("", response_model=ConversationOut, status_code=201)
def create_conversation(
    data: ConversationCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ConversationOut:
    result = ConversationService(db).create_or_get(user, data.user_id)
    if result.is_new:
        # WS-список «партнерів для сповіщень про присутність» кожного клієнта формюється один
        # раз при підключенні (app/websocket/chat.py) і ще не знав про щойно створений діалог —
        # тому надсилаємо поточний онлайн-статус одноразово в момент його появи.
        if manager.is_online(result.partner_id):
            anyio.from_thread.run(
                manager.send_to_user, user.id, events.user_online(result.partner_id)
            )
        if manager.is_online(user.id):
            anyio.from_thread.run(
                manager.send_to_user, result.partner_id, events.user_online(user.id)
            )
    return result.conversation


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ConversationOut:
    return ConversationService(db).get_one(user, conversation_id)


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    ConversationService(db).delete(user, conversation_id)
