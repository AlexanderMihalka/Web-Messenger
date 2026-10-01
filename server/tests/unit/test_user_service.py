"""UserService: профіль, пошук, блокування користувачів."""

import pytest
from sqlalchemy.orm import Session

from app.schemas.user import UserUpdate
from app.services.exceptions import Conflict, NotFound
from app.services.user_service import UserService
from tests.conftest import make_user


def test_update_me_partial_update_only_touches_given_fields(db: Session) -> None:
    user = make_user(db, username="alice", display_name="Alice")
    service = UserService(db)
    updated = service.update_me(user, UserUpdate(bio="Hello there"))
    assert updated.bio == "Hello there"
    assert updated.display_name == "Alice"  # не чіпали — лишилось як було


def test_update_me_username_conflict(db: Session) -> None:
    make_user(db, username="taken")
    user = make_user(db, username="alice")
    with pytest.raises(Conflict):
        UserService(db).update_me(user, UserUpdate(username="taken"))


def test_update_me_can_keep_same_username(db: Session) -> None:
    user = make_user(db, username="alice")
    updated = UserService(db).update_me(user, UserUpdate(username="alice"))
    assert updated.username == "alice"


def test_block_then_unblock_round_trip(db: Session) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    service = UserService(db)

    service.block(alice, bob.id)
    assert any(u.id == bob.id for u in service.list_blocked(alice))

    service.unblock(alice, bob.id)
    assert service.list_blocked(alice) == []


def test_block_is_idempotent(db: Session) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    service = UserService(db)
    service.block(alice, bob.id)
    service.block(alice, bob.id)  # не повинно кидати помилку чи дублювати запис
    assert len(service.list_blocked(alice)) == 1


def test_block_rejects_self(db: Session) -> None:
    alice = make_user(db, username="alice")
    with pytest.raises(Conflict):
        UserService(db).block(alice, alice.id)


def test_search_excludes_self_and_blocked_users(db: Session) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob_smith")
    make_user(db, username="alice2")  # інший юзер, не має збігатись з "alice" пошуком по собі

    results = UserService(db).search(alice.id, "bob")
    assert [u.id for u in results] == [bob.id]

    self_results = UserService(db).search(alice.id, "alice")
    assert alice.id not in [u.id for u in self_results]


def test_get_public_missing_user_raises(db: Session) -> None:
    with pytest.raises(NotFound):
        UserService(db).get_public(999_999)
