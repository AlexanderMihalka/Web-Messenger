"""/api/v1/users — профіль, пошук, аватар, блокування (HTTP-рівень)."""

import io

from fastapi.testclient import TestClient
from PIL import Image

from tests.conftest import auth_headers, make_user


def _png_bytes(size: tuple[int, int] = (64, 64), color: str = "red") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color=color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_search_finds_by_username_or_display_name(client: TestClient, db) -> None:
    make_user(db, username="alice")
    make_user(db, username="bobby", display_name="Bob Marley")
    headers = auth_headers(client, "alice")

    response = client.get("/api/v1/users/search", params={"q": "marley"}, headers=headers)
    assert response.status_code == 200
    assert [u["username"] for u in response.json()] == ["bobby"]


def test_update_me_patch(client: TestClient, db) -> None:
    make_user(db, username="alice")
    headers = auth_headers(client, "alice")
    response = client.patch("/api/v1/users/me", json={"bio": "Hello!"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["bio"] == "Hello!"


def test_update_me_rejects_taken_username(client: TestClient, db) -> None:
    make_user(db, username="alice")
    make_user(db, username="bob")
    headers = auth_headers(client, "alice")
    response = client.patch("/api/v1/users/me", json={"username": "bob"}, headers=headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_avatar_upload_accepts_valid_image(client: TestClient, db) -> None:
    make_user(db, username="alice")
    headers = auth_headers(client, "alice")
    response = client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 200, response.text
    avatar_url = response.json()["avatar_url"]
    assert avatar_url.startswith("/uploads/avatars/")

    served = client.get(avatar_url)
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/png"


def test_avatar_upload_rejects_non_image_disguised_as_png(client: TestClient, db) -> None:
    make_user(db, username="alice")
    headers = auth_headers(client, "alice")
    response = client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", b"not actually a png file", "image/png")},
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_avatar_upload_rejects_oversized_file(client: TestClient, db, monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "max_avatar_bytes", 100)
    make_user(db, username="alice")
    headers = auth_headers(client, "alice")
    response = client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", _png_bytes((200, 200)), "image/png")},
    )
    assert response.status_code == 413


def test_block_prevents_partner_from_listing_me_publicly(client: TestClient, db) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    headers = auth_headers(client, "alice")

    response = client.post(f"/api/v1/users/{bob.id}/block", headers=headers)
    assert response.status_code == 201

    listed = client.get("/api/v1/users", headers=headers).json()
    assert bob.id not in [u["id"] for u in listed["items"]]

    unblock = client.delete(f"/api/v1/users/{bob.id}/block", headers=headers)
    assert unblock.status_code == 200
    assert unblock.json()["id"] == bob.id
