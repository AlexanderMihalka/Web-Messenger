"""/api/v1/conversations — HTTP-рівень."""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, make_user


def test_create_list_get_delete_conversation(client: TestClient, db) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    headers = auth_headers(client, "alice")

    created = client.post("/api/v1/conversations", json={"user_id": bob.id}, headers=headers)
    assert created.status_code == 201, created.text
    conversation_id = created.json()["id"]
    assert created.json()["partner"]["id"] == bob.id

    again = client.post("/api/v1/conversations", json={"user_id": bob.id}, headers=headers)
    assert again.status_code == 201
    assert again.json()["id"] == conversation_id  # ідемпотентно, не дублюється

    listing = client.get("/api/v1/conversations", headers=headers)
    assert listing.status_code == 200
    assert [c["id"] for c in listing.json()] == [conversation_id]

    fetched = client.get(f"/api/v1/conversations/{conversation_id}", headers=headers)
    assert fetched.status_code == 200

    deleted = client.delete(f"/api/v1/conversations/{conversation_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get("/api/v1/conversations", headers=headers).json() == []


def test_create_conversation_with_self_is_conflict(client: TestClient, db) -> None:
    alice = make_user(db, username="alice")
    headers = auth_headers(client, "alice")
    response = client.post("/api/v1/conversations", json={"user_id": alice.id}, headers=headers)
    assert response.status_code == 409


def test_stranger_cannot_read_someone_elses_conversation(client: TestClient, db) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    make_user(db, username="carol", password="Secret123")
    headers = auth_headers(client, "alice")
    conversation_id = client.post(
        "/api/v1/conversations", json={"user_id": bob.id}, headers=headers
    ).json()["id"]

    carol_headers = auth_headers(client, "carol")
    response = client.get(f"/api/v1/conversations/{conversation_id}", headers=carol_headers)
    assert response.status_code == 404  # не 403 — не підтверджуємо навіть існування діалогу
