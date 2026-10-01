"""Приватні діалоги: список, створення (ідемпотентне), перегляд, приховання.

Сервіс лишається синхронним і не знає про WebSocket — розсилку подій виконує роутер
після виклику сервісу (див. app/routers/conversations.py). Це дозволяє юніт-тестувати
сервіс без запущеного event loop.
"""

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import ConversationMember, User
from app.repositories.block_repository import BlockRepository
from app.repositories.conversation_repository import ConversationRepository, direct_key
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.conversation import ConversationOut
from app.services.exceptions import Conflict, NotFound
from app.services.mappers import to_message_out, to_user_public

# Створення/приховання діалогу — рутинна активність користувача, не подія безпеки: лишається
# лише в stdout (docker logs), у таблицю audit_logs (GET /admin/logs) не пишеться, щоб не
# «топити» там дійсно важливі події (автентифікацію, блокування, дії адміністратора).
audit_log = logging.getLogger("messenger.audit")


@dataclass
class CreateConversationResult:
    conversation: ConversationOut
    is_new: bool
    partner_id: int


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.conversations = ConversationRepository(db)
        self.messages = MessageRepository(db)
        self.users = UserRepository(db)
        self.blocks = BlockRepository(db)

    def list_for_user(self, actor: User) -> list[ConversationOut]:
        memberships = self.conversations.memberships(actor.id)
        conversation_ids = [m.conversation_id for m in memberships]
        if not conversation_ids:
            return []

        conversations = self.conversations.by_ids(conversation_ids)
        partner_members = self.conversations.partner_members(conversation_ids, actor.id)
        partner_ids = {m.user_id for m in partner_members.values()}
        partners = {pid: self.users.get(pid) for pid in partner_ids}
        last_messages = self.conversations.last_messages(conversation_ids)
        unread = self.conversations.unread_counts(actor.id, conversation_ids)
        by_me, blocked_me = self.blocks.related_ids(actor.id)

        out: list[ConversationOut] = []
        for member in memberships:
            conversation = conversations.get(member.conversation_id)
            partner_member = partner_members.get(member.conversation_id)
            if conversation is None or partner_member is None:
                continue
            partner = partners.get(partner_member.user_id)
            if partner is None:
                continue
            last = last_messages.get(conversation.id)
            pair = {actor.id: member, partner_member.user_id: partner_member}
            out.append(
                ConversationOut(
                    id=conversation.id,
                    partner=to_user_public(partner),
                    last_message=to_message_out(last, members=pair) if last else None,
                    unread_count=unread.get(conversation.id, 0),
                    updated_at=last.created_at if last else conversation.created_at,
                    blocked_by_me=partner.id in by_me,
                    can_send=partner.id not in by_me and partner.id not in blocked_me,
                )
            )
        out.sort(key=lambda c: c.updated_at, reverse=True)
        return out

    def create_or_get(self, actor: User, partner_id: int) -> CreateConversationResult:
        if partner_id == actor.id:
            raise Conflict("Не можна створити діалог із самим собою")
        partner = self.users.get(partner_id)
        if partner is None:
            raise NotFound("Користувача не знайдено")

        key = direct_key(actor.id, partner_id)
        conversation = self.conversations.get_by_key(key)
        is_new = conversation is None
        if conversation is None:
            conversation = self.conversations.create_direct(key, (actor.id, partner_id))
            self.db.commit()
            audit_log.info(
                "conversation_create id=%s user_a=%s user_b=%s", conversation.id, actor.id, partner_id
            )
        else:
            member = self.conversations.get_member(conversation.id, actor.id)
            if member is not None and member.is_hidden:
                member.is_hidden = False
                self.db.commit()

        out = self._build_single(actor, conversation.id)
        return CreateConversationResult(conversation=out, is_new=is_new, partner_id=partner_id)

    def get_one(self, actor: User, conversation_id: int) -> ConversationOut:
        return self._build_single(actor, conversation_id)

    def delete(self, actor: User, conversation_id: int) -> None:
        member = self._require_membership(actor.id, conversation_id)
        member.is_hidden = True
        self.db.commit()
        audit_log.info("conversation_hide id=%s user_id=%s", conversation_id, actor.id)

    # -- internal -----------------------------------------------------

    def _require_membership(self, user_id: int, conversation_id: int) -> ConversationMember:
        member = self.conversations.get_member(conversation_id, user_id)
        if member is None:
            raise NotFound("Діалог не знайдено")
        return member

    def _build_single(self, actor: User, conversation_id: int) -> ConversationOut:
        member = self._require_membership(actor.id, conversation_id)
        conversation = self.conversations.get(conversation_id)
        assert conversation is not None
        partner_member = next(
            (m for m in self.conversations.get_members(conversation_id) if m.user_id != actor.id),
            None,
        )
        if partner_member is None:
            raise NotFound("Діалог не знайдено")
        partner = self.users.get(partner_member.user_id)
        if partner is None:
            raise NotFound("Співрозмовника не знайдено")
        last = self.conversations.last_messages([conversation_id]).get(conversation_id)
        unread = self.conversations.unread_counts(actor.id, [conversation_id]).get(conversation_id, 0)
        can_send = not self.blocks.exists_between(actor.id, partner.id)
        blocked_by_me = self.blocks.get(actor.id, partner.id) is not None
        pair = {actor.id: member, partner_member.user_id: partner_member}
        return ConversationOut(
            id=conversation.id,
            partner=to_user_public(partner),
            last_message=to_message_out(last, members=pair) if last else None,
            unread_count=unread,
            updated_at=last.created_at if last else conversation.created_at,
            blocked_by_me=blocked_by_me,
            can_send=can_send,
        )
