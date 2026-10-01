"""ORM -> Pydantic. Онлайн-статус ніколи не зберігається в БД — завжди читається з менеджера
активних WebSocket-зʼєднань, тому не може розсинхронізуватися з реальним станом зʼєднань."""

from app.models import ConversationMember, Message, User
from app.schemas.message import MessageOut
from app.schemas.user import UserMe, UserPublic
from app.websocket.manager import manager


def to_user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        is_online=manager.is_online(user.id),
        last_seen_at=user.last_seen_at,
        created_at=user.created_at,
    )


def to_user_me(user: User) -> UserMe:
    return UserMe(
        **to_user_public(user).model_dump(),
        email=user.email,
        role=user.role.value,
        is_blocked=user.is_blocked,
    )


def to_message_out(message: Message, *, members: dict[int, ConversationMember]) -> MessageOut:
    """`is_read` завжди означає «чи прочитав повідомлення отримувач» (checkmarks-семантика),
    а не «чи прочитав його той, хто зараз дивиться» — тому воно однакове для обох учасників
    і той самий MessageOut можна розсилати по WebSocket без перерахунку під кожного глядача.
    Отримувач = учасник діалогу, що не є відправником; у приватному чаті він завжди один."""
    recipient = next((m for uid, m in members.items() if uid != message.sender_id), None)
    is_read = recipient is not None and message.id <= recipient.last_read_message_id
    deleted = message.deleted_at is not None
    return MessageOut(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        content="" if deleted else message.content,
        created_at=message.created_at,
        updated_at=message.updated_at,
        is_edited=message.is_edited,
        is_deleted=deleted,
        is_read=is_read,
    )
