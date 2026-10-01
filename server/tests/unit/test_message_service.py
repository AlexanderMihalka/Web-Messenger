"""MessageService: надсилання, редагування, видалення, читання, пагінація, блокування."""

import pytest
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.services.conversation_service import ConversationService
from app.services.exceptions import Blocked, Forbidden, NotFound
from app.services.message_service import MessageService
from app.services.user_service import UserService
from tests.conftest import make_user


@pytest.fixture
def users(db: Session) -> tuple[int, int]:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    return alice.id, bob.id


@pytest.fixture
def conversation_id(db: Session, users: tuple[int, int]) -> int:
    alice_id, bob_id = users
    alice = UserRepository(db).get(alice_id)
    assert alice is not None
    return ConversationService(db).create_or_get(alice, bob_id).conversation.id


def _user(db: Session, user_id: int):
    user = UserRepository(db).get(user_id)
    assert user is not None
    return user


def test_send_persists_message_readable_by_both_sides(
    db: Session, users: tuple[int, int], conversation_id: int
) -> None:
    alice_id, bob_id = users
    out = MessageService(db).send(_user(db, alice_id), conversation_id, "Привіт, Боб!")
    assert out.content == "Привіт, Боб!"
    assert out.sender_id == alice_id
    assert out.is_read is False  # Боб ще не читав

    page = MessageService(db).list_page(_user(db, bob_id), conversation_id, 0, None, 50)
    assert len(page.items) == 1
    assert page.items[0].content == "Привіт, Боб!"


def test_send_rejects_empty_conversation_membership(db: Session, users: tuple[int, int]) -> None:
    alice_id, _ = users
    stranger = make_user(db, username="stranger")
    with pytest.raises(NotFound):
        MessageService(db).send(stranger, 999_999, "hi")


def test_send_blocked_in_either_direction_is_rejected(
    db: Session, users: tuple[int, int], conversation_id: int
) -> None:
    alice_id, bob_id = users
    UserService(db).block(_user(db, alice_id), bob_id)
    with pytest.raises(Blocked):
        MessageService(db).send(_user(db, bob_id), conversation_id, "can I still text?")
    with pytest.raises(Blocked):
        MessageService(db).send(_user(db, alice_id), conversation_id, "nor can I")


def test_edit_only_own_message(db: Session, users: tuple[int, int], conversation_id: int) -> None:
    alice_id, bob_id = users
    message = MessageService(db).send(_user(db, alice_id), conversation_id, "oops")
    edited = MessageService(db).edit(_user(db, alice_id), message.id, "fixed")
    assert edited.content == "fixed"
    assert edited.is_edited is True

    with pytest.raises(Forbidden):
        MessageService(db).edit(_user(db, bob_id), message.id, "hacked")


def test_delete_clears_content_but_keeps_row(
    db: Session, users: tuple[int, int], conversation_id: int
) -> None:
    alice_id, _ = users
    message = MessageService(db).send(_user(db, alice_id), conversation_id, "secret")
    deleted = MessageService(db).delete(_user(db, alice_id), message.id)
    assert deleted.is_deleted is True
    assert deleted.content == ""


def test_mark_read_updates_cursor_and_unread_count(
    db: Session, users: tuple[int, int], conversation_id: int
) -> None:
    alice_id, bob_id = users
    service = MessageService(db)
    m1 = service.send(_user(db, alice_id), conversation_id, "one")
    service.send(_user(db, alice_id), conversation_id, "two")

    result = service.mark_read(_user(db, bob_id), m1.id)
    assert result.last_read_message_id == m1.id
    assert result.unread_count == 1  # друге повідомлення ще не прочитане


def test_list_page_initial_load_returns_most_recent_tail(
    db: Session, users: tuple[int, int], conversation_id: int
) -> None:
    """Без параметрів пагінації — як при відкритті діалогу: показуємо хвіст (найновіші),
    у хронологічному порядку, з прапорцем, що вище є ще старіша історія."""
    alice_id, bob_id = users
    service = MessageService(db)
    ids = [service.send(_user(db, alice_id), conversation_id, f"msg {i}").id for i in range(5)]

    page = service.list_page(_user(db, bob_id), conversation_id, 0, None, 2)
    assert [m.id for m in page.items] == ids[3:5]
    assert page.has_more is True


def test_list_page_before_id_scrolls_to_older_history(
    db: Session, users: tuple[int, int], conversation_id: int
) -> None:
    """`before_id` — гортання вгору: наступна (старіша) сторінка, теж у хронологічному порядку."""
    alice_id, bob_id = users
    service = MessageService(db)
    ids = [service.send(_user(db, alice_id), conversation_id, f"msg {i}").id for i in range(5)]

    older_page = service.list_page(_user(db, bob_id), conversation_id, 0, ids[3], 2)
    assert [m.id for m in older_page.items] == ids[1:3]
    assert older_page.has_more is True

    oldest_page = service.list_page(_user(db, bob_id), conversation_id, 0, ids[1], 2)
    assert [m.id for m in oldest_page.items] == ids[0:1]
    assert oldest_page.has_more is False


def test_list_page_after_id_without_before_paginates_forward(
    db: Session, users: tuple[int, int], conversation_id: int
) -> None:
    """Лише `after_id` (без `before_id`) — «наздогнати» пропущене після реконекту:
    наступні повідомлення вперед від цієї точки, а не хвіст усього діалогу."""
    alice_id, bob_id = users
    service = MessageService(db)
    ids = [service.send(_user(db, alice_id), conversation_id, f"msg {i}").id for i in range(5)]

    catch_up = service.list_page(_user(db, bob_id), conversation_id, ids[1], None, 2)
    assert [m.id for m in catch_up.items] == ids[2:4]
    assert catch_up.has_more is True
