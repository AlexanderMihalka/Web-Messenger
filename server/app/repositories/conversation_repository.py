from collections.abc import Sequence

from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import Session

from app.models import Conversation, ConversationMember, Message


def direct_key(a: int, b: int) -> str:
    low, high = sorted((a, b))
    return f"{low}:{high}"


class ConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, conversation_id: int) -> Conversation | None:
        return self.db.get(Conversation, conversation_id)

    def get_by_key(self, key: str) -> Conversation | None:
        return self.db.scalar(select(Conversation).where(Conversation.direct_key == key))

    def create_direct(self, key: str, user_ids: tuple[int, int]) -> Conversation:
        conversation = Conversation(direct_key=key)
        self.db.add(conversation)
        self.db.flush()
        for user_id in user_ids:
            self.db.add(ConversationMember(conversation_id=conversation.id, user_id=user_id))
        self.db.flush()
        return conversation

    def get_members(self, conversation_id: int) -> list[ConversationMember]:
        stmt = select(ConversationMember).where(ConversationMember.conversation_id == conversation_id)
        return list(self.db.scalars(stmt))

    def get_member(self, conversation_id: int, user_id: int) -> ConversationMember | None:
        return self.db.scalar(
            select(ConversationMember).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
        )

    def memberships(
        self,
        user_id: int,
        *,
        conversation_id: int | None = None,
        include_hidden: bool = False,
    ) -> list[ConversationMember]:
        stmt = select(ConversationMember).where(ConversationMember.user_id == user_id)
        if conversation_id is not None:
            stmt = stmt.where(ConversationMember.conversation_id == conversation_id)
        if not include_hidden:
            stmt = stmt.where(ConversationMember.is_hidden.is_(False))
        return list(self.db.scalars(stmt))

    def partner_members(
        self, conversation_ids: Sequence[int], user_id: int
    ) -> dict[int, ConversationMember]:
        if not conversation_ids:
            return {}
        rows = self.db.scalars(
            select(ConversationMember).where(
                ConversationMember.conversation_id.in_(conversation_ids),
                ConversationMember.user_id != user_id,
            )
        )
        return {member.conversation_id: member for member in rows}

    def by_ids(self, ids: Sequence[int]) -> dict[int, Conversation]:
        if not ids:
            return {}
        rows = self.db.scalars(select(Conversation).where(Conversation.id.in_(ids)))
        return {conversation.id: conversation for conversation in rows}

    def last_messages(self, conversation_ids: Sequence[int]) -> dict[int, Message]:
        """Останнє (за id) повідомлення кожного діалогу — включно з видаленими (щоб у списку
        чатів показати «Повідомлення видалено», як роблять інші месенджери)."""
        if not conversation_ids:
            return {}
        last_ids = (
            select(func.max(Message.id))
            .where(Message.conversation_id.in_(conversation_ids))
            .group_by(Message.conversation_id)
        )
        rows = self.db.scalars(select(Message).where(Message.id.in_(last_ids)))
        return {message.conversation_id: message for message in rows}

    def unread_counts(self, user_id: int, conversation_ids: Sequence[int]) -> dict[int, int]:
        if not conversation_ids:
            return {}
        cm = ConversationMember
        stmt = (
            select(Message.conversation_id, func.count(Message.id))
            .join(cm, and_(cm.conversation_id == Message.conversation_id, cm.user_id == user_id))
            .where(
                Message.conversation_id.in_(conversation_ids),
                Message.sender_id.is_not(None),
                Message.sender_id != user_id,
                Message.deleted_at.is_(None),
                Message.id > cm.last_read_message_id,
            )
            .group_by(Message.conversation_id)
        )
        return {conversation_id: count for conversation_id, count in self.db.execute(stmt).all()}

    def partner_ids(self, user_id: int) -> list[int]:
        """Усі користувачі, з якими є спільні діалоги (для розсилки присутності)."""
        mine = select(ConversationMember.conversation_id).where(
            ConversationMember.user_id == user_id
        )
        stmt = (
            select(ConversationMember.user_id)
            .where(ConversationMember.conversation_id.in_(mine), ConversationMember.user_id != user_id)
            .distinct()
        )
        return list(self.db.scalars(stmt))

    def conversation_ids_of(self, user_id: int) -> list[int]:
        return list(
            self.db.scalars(
                select(ConversationMember.conversation_id).where(
                    ConversationMember.user_id == user_id
                )
            )
        )

    def delete_conversations(self, ids: Sequence[int]) -> None:
        if not ids:
            return
        self.db.execute(delete(Message).where(Message.conversation_id.in_(ids)))
        self.db.execute(
            delete(ConversationMember).where(ConversationMember.conversation_id.in_(ids))
        )
        self.db.execute(delete(Conversation).where(Conversation.id.in_(ids)))
