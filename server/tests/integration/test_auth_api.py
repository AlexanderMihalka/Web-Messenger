"""/api/v1/auth — HTTP-рівень: реєстрація, вхід, refresh-cookie, logout, /me."""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, make_user


def test_register_returns_token_and_sets_refresh_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "Secret123",
            "confirm_password": "Secret123",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert "refresh_token" in response.cookies


def test_register_rejects_password_mismatch(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "Secret123",
            "confirm_password": "Different123",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_register_rejects_weak_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "short",
            "confirm_password": "short",
        },
    )
    assert response.status_code == 422


def test_login_then_me_returns_profile(client: TestClient, db) -> None:
    make_user(db, username="alice", password="Secret123")
    headers = auth_headers(client, "alice")
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_me_without_token_is_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_login_wrong_password_is_404_style_not_found_message(client: TestClient, db) -> None:
    make_user(db, username="alice", password="Secret123")
    response = client.post("/api/v1/auth/login", json={"login": "alice", "password": "WrongPass1"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_refresh_cookie_flow_rotates_token(client: TestClient, db) -> None:
    make_user(db, username="alice", password="Secret123")
    login = client.post("/api/v1/auth/login", json={"login": "alice", "password": "Secret123"})
    old_access = login.json()["access_token"]

    refreshed = client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"] != old_access


def test_refresh_without_cookie_or_body_is_401(client: TestClient) -> None:
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_logout_clears_cookie_and_revokes_session(client: TestClient, db) -> None:
    make_user(db, username="alice", password="Secret123")
    login = client.post("/api/v1/auth/login", json={"login": "alice", "password": "Secret123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    logout = client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 204

    refreshed = client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 401
