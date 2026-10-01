"""/api/v1/admin — доступ лише для ADMIN, керування користувачами, статистика, журнали."""

from fastapi.testclient import TestClient

from app.models import UserRole
from tests.conftest import auth_headers, make_user


def test_regular_user_is_forbidden(client: TestClient, db) -> None:
    make_user(db, username="alice")
    headers = auth_headers(client, "alice")
    response = client.get("/api/v1/admin/statistics", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_admin_can_list_users_and_see_statistics(client: TestClient, db) -> None:
    make_user(db, username="root", role=UserRole.ADMIN)
    make_user(db, username="alice")
    headers = auth_headers(client, "root")

    users = client.get("/api/v1/admin/users", headers=headers)
    assert users.status_code == 200
    assert users.json()["total"] == 2

    stats = client.get("/api/v1/admin/statistics", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["total_users"] == 2


def test_admin_block_and_delete_user(client: TestClient, db) -> None:
    make_user(db, username="root", role=UserRole.ADMIN)
    target = make_user(db, username="alice", password="Secret123")
    headers = auth_headers(client, "root")

    blocked = client.patch(
        f"/api/v1/admin/users/{target.id}/block", json={"blocked": True}, headers=headers
    )
    assert blocked.status_code == 200
    assert blocked.json()["is_blocked"] is True

    login_attempt = client.post(
        "/api/v1/auth/login", json={"login": "alice", "password": "Secret123"}
    )
    assert login_attempt.status_code == 403

    deleted = client.delete(f"/api/v1/admin/users/{target.id}", headers=headers)
    assert deleted.status_code == 204

    listing = client.get("/api/v1/admin/users", headers=headers).json()
    assert target.id not in [u["id"] for u in listing["items"]]


def test_admin_actions_are_logged(client: TestClient, db) -> None:
    make_user(db, username="root", role=UserRole.ADMIN)
    target = make_user(db, username="alice")
    headers = auth_headers(client, "root")

    client.patch(f"/api/v1/admin/users/{target.id}/block", json={"blocked": True}, headers=headers)

    logs = client.get("/api/v1/admin/logs", params={"event": "admin_block"}, headers=headers)
    assert logs.status_code == 200
    assert logs.json()["total"] >= 1
