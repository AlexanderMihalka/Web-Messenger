"""Надсилання, редагування, видалення, читання повідомлень.

Синхронний сервіс без прямого доступу до WebSocket-менеджера (як і conversation_service) —
роутер сам розсилає події після успішної мутації (див. app/routers/messages.py).
"""

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import ConversationMember, Message, User
from app.repositories.block_repository import BlockRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.message import MessageOut, MessagePage, ReadResult
from app.services.exceptions import Blocked, Forbidden, NotFound
from app.services.mappers import to_message_out

audit_log = logging.getLogger("messenger.audit")

MAX_PAGE_SIZE = 100


class MessageService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.conversations = ConversationRepository(db)
        self.messages = MessageRepository(db)
        self.blocks = BlockRepository(db)

    def send(self, actor: User, conversation_id: int, content: str) -> MessageOut:
        members = self._members(conversation_id, actor.id)
        partner_id = self._other_user_id(members, actor.id)
        if self.blocks.exists_between(actor.id, partner_id):
            raise Blocked("Надсилання неможливе: користувача заблоковано")

        message = Message(conversation_id=conversation_id, sender_id=actor.id, content=content)
        self.messages.add(message)
        # Новий діалог знову зʼявляється у списку, навіть якщо його раніше приховали.
        for member in members.values():
            member.is_hidden = False
        self.db.commit()
        self.db.refresh(message)
        audit_log.info(
            "message_send id=%s conversation_id=%s sender_id=%s", message.id, conversation_id, actor.id
        )
        return to_message_out(message, members=members)

    def edit(self, actor: User, message_id: int, content: str) -> MessageOut:
        message, members = self._require_own_message(actor.id, message_id)
        if message.deleted_at is not None:
            raise NotFound("Повідомлення не знайдено")
        message.content = content
        message.is_edited = True
        message.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(message)
        audit_log.info("message_edit id=%s user_id=%s", message_id, actor.id)
        return to_message_out(message, members=members)

    def delete(self, actor: User, message_id: int) -> MessageOut:
        message, members = self._require_own_message(actor.id, message_id)
        if message.deleted_at is None:
            message.deleted_at = datetime.now(UTC)
            message.content = ""
            self.db.commit()
            self.db.refresh(message)
            audit_log.info("message_delete id=%s user_id=%s", message_id, actor.id)
        return to_message_out(message, members=members)

    def mark_read(self, actor: User, message_id: int) -> ReadResult:
        message = self.messages.get(message_id)
        if message is None:
            raise NotFound("Повідомлення не знайдено")
        member = self._require_membership(actor.id, message.conversation_id)
        if message.id > member.last_read_message_id:
            member.last_read_message_id = message.id
            member.last_read_at = datetime.now(UTC)
            self.db.commit()
        unread = self.conversations.unread_counts(actor.id, [message.conversation_id])
        return ReadResult(
            conversation_id=message.conversation_id,
            last_read_message_id=member.last_read_message_id,
            unread_count=unread.get(message.conversation_id, 0),
        )

    def list_page(
        self, actor: User, conversation_id: int, after_id: int, before_id: int | None, limit: int
    ) -> MessagePage:
        members = self._members(conversation_id, actor.id)
        limit = max(1, min(limit, MAX_PAGE_SIZE))
        rows, has_more = self.messages.page(conversation_id, after_id, before_id, limit)
        return MessagePage(items=[to_message_out(m, members=members) for m in rows], has_more=has_more)

    # -- internal -----------------------------------------------------

    def _require_membership(self, user_id: int, conversation_id: int) -> ConversationMember:
        member = self.conversations.get_member(conversation_id, user_id)
        if member is None:
            raise NotFound("Діалог не знайдено")
        return member

    def _members(self, conversation_id: int, user_id: int) -> dict[int, ConversationMember]:
        """Обидва учасники приватного діалогу, ключ — user_id. Кидає NotFound, якщо
        викликач сам не є учасником (не можна дізнатись про чужий діалог за id)."""
        rows = self.conversations.get_members(conversation_id)
        by_user = {m.user_id: m for m in rows}
        if user_id not in by_user:
            raise NotFound("Діалог не знайдено")
        return by_user

    @staticmethod
    def _other_user_id(members: dict[int, ConversationMember], user_id: int) -> int:
        other = next((uid for uid in members if uid != user_id), None)
        if other is None:
            raise NotFound("Діалог не знайдено")
        return other

    def _require_own_message(
        self, user_id: int, message_id: int
    ) -> tuple[Message, dict[int, ConversationMember]]:
        message = self.messages.get(message_id)
        if message is None:
            raise NotFound("Повідомлення не знайдено")
        members = self._members(message.conversation_id, user_id)
        if message.sender_id != user_id:
            raise Forbidden("Можна редагувати або видаляти лише власні повідомлення")
        return message, members
