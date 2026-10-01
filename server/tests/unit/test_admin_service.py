"""AdminService: керування користувачами та статистика — лише для адміністратора."""

import pytest
from sqlalchemy.orm import Session

from app.models import UserRole
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from app.services.exceptions import Conflict, Forbidden, NotFound
from tests.conftest import make_user


def test_set_blocked_true_then_false(db: Session) -> None:
    admin = make_user(db, username="root", role=UserRole.ADMIN)
    target = make_user(db, username="alice", password="Secret123")
    service = AdminService(db)

    blocked = service.set_blocked(admin, target.id, True)
    assert blocked.is_blocked is True

    with pytest.raises(Forbidden):
        AuthService(db).login("alice", "Secret123", ip="127.0.0.1")

    unblocked = service.set_blocked(admin, target.id, False)
    assert unblocked.is_blocked is False


def test_set_blocked_revokes_active_sessions(db: Session) -> None:
    admin = make_user(db, username="root", role=UserRole.ADMIN)
    target = make_user(db, username="alice", password="Secret123")
    auth = AuthService(db)
    session = auth.login("alice", "Secret123", ip="127.0.0.1")

    AdminService(db).set_blocked(admin, target.id, True)

    from app.services.exceptions import NotFound as SvcNotFound

    with pytest.raises(SvcNotFound):
        auth.refresh(session.refresh_token, ip="127.0.0.1")


def test_admin_cannot_block_self(db: Session) -> None:
    admin = make_user(db, username="root", role=UserRole.ADMIN)
    with pytest.raises(Conflict):
        AdminService(db).set_blocked(admin, admin.id, True)


def test_admin_cannot_block_another_admin(db: Session) -> None:
    admin = make_user(db, username="root", role=UserRole.ADMIN)
    other_admin = make_user(db, username="root2", role=UserRole.ADMIN)
    with pytest.raises(Forbidden):
        AdminService(db).set_blocked(admin, other_admin.id, True)


def test_delete_user_removes_account(db: Session) -> None:
    admin = make_user(db, username="root", role=UserRole.ADMIN)
    target = make_user(db, username="alice")
    AdminService(db).delete_user(admin, target.id)
    with pytest.raises(NotFound):
        from app.services.user_service import UserService

        UserService(db).get_public(target.id)


def test_delete_user_rejects_self_and_admins(db: Session) -> None:
    admin = make_user(db, username="root", role=UserRole.ADMIN)
    other_admin = make_user(db, username="root2", role=UserRole.ADMIN)
    with pytest.raises(Conflict):
        AdminService(db).delete_user(admin, admin.id)
    with pytest.raises(Forbidden):
        AdminService(db).delete_user(admin, other_admin.id)


def test_statistics_counts_users_and_conversations(db: Session) -> None:
    make_user(db, username="root", role=UserRole.ADMIN)
    make_user(db, username="alice")
    make_user(db, username="bob")
    stats = AdminService(db).statistics()
    assert stats.total_users == 3
    assert stats.admins == 1
