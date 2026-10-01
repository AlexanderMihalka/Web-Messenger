"""ConversationService: створення/ідемпотентність, список, приховання."""

import pytest
from sqlalchemy.orm import Session

from app.services.conversation_service import ConversationService
from app.services.exceptions import Conflict, NotFound
from app.services.message_service import MessageService
from tests.conftest import make_user


def test_create_or_get_is_idempotent_both_directions(db: Session) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    service = ConversationService(db)

    first = service.create_or_get(alice, bob.id)
    assert first.is_new is True

    again = service.create_or_get(alice, bob.id)
    assert again.is_new is False
    assert again.conversation.id == first.conversation.id

    from_bob_side = service.create_or_get(bob, alice.id)
    assert from_bob_side.conversation.id == first.conversation.id


def test_create_or_get_rejects_self(db: Session) -> None:
    alice = make_user(db, username="alice")
    with pytest.raises(Conflict):
        ConversationService(db).create_or_get(alice, alice.id)


def test_create_or_get_rejects_missing_partner(db: Session) -> None:
    alice = make_user(db, username="alice")
    with pytest.raises(NotFound):
        ConversationService(db).create_or_get(alice, 999_999)


def test_list_for_user_reports_unread_count_and_ordering(db: Session) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    conv_service = ConversationService(db)
    msg_service = MessageService(db)

    conversation = conv_service.create_or_get(alice, bob.id).conversation
    msg_service.send(bob, conversation.id, "Привіт!")
    msg_service.send(bob, conversation.id, "Як справи?")

    listing = conv_service.list_for_user(alice)
    assert len(listing) == 1
    assert listing[0].unread_count == 2
    assert listing[0].last_message is not None
    assert listing[0].last_message.content == "Як справи?"


def test_get_one_requires_membership(db: Session) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    carol = make_user(db, username="carol")
    conversation = ConversationService(db).create_or_get(alice, bob.id).conversation
    with pytest.raises(NotFound):
        ConversationService(db).get_one(carol, conversation.id)


def test_delete_hides_conversation_until_new_message_arrives(db: Session) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    conv_service = ConversationService(db)
    msg_service = MessageService(db)

    conversation = conv_service.create_or_get(alice, bob.id).conversation
    conv_service.delete(alice, conversation.id)
    assert conv_service.list_for_user(alice) == []

    msg_service.send(bob, conversation.id, "Привіт знову")
    listing = conv_service.list_for_user(alice)
    assert len(listing) == 1
    assert listing[0].id == conversation.id
