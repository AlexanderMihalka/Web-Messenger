"""/api/v1/conversations/{id}/messages, /api/v1/messages/{id} — HTTP-рівень."""

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, make_user


def _conversation_id(client: TestClient, headers: dict[str, str], partner_id: int) -> int:
    response = client.post("/api/v1/conversations", json={"user_id": partner_id}, headers=headers)
    result: int = response.json()["id"]
    return result


def test_send_list_edit_delete_read_message(client: TestClient, db) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    alice_headers = auth_headers(client, "alice")
    bob_headers = auth_headers(client, "bob")
    conversation_id = _conversation_id(client, alice_headers, bob.id)

    sent = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Привіт!"},
        headers=alice_headers,
    )
    assert sent.status_code == 201, sent.text
    message_id = sent.json()["id"]
    assert sent.json()["is_read"] is False

    listing = client.get(f"/api/v1/conversations/{conversation_id}/messages", headers=bob_headers)
    assert listing.status_code == 200
    assert len(listing.json()["items"]) == 1

    edited = client.patch(
        f"/api/v1/messages/{message_id}", json={"content": "Привіт, Бобе!"}, headers=alice_headers
    )
    assert edited.status_code == 200
    assert edited.json()["is_edited"] is True

    bob_cannot_edit = client.patch(
        f"/api/v1/messages/{message_id}", json={"content": "hacked"}, headers=bob_headers
    )
    assert bob_cannot_edit.status_code == 403

    read = client.post(f"/api/v1/messages/{message_id}/read", headers=bob_headers)
    assert read.status_code == 200
    assert read.json()["unread_count"] == 0

    deleted = client.delete(f"/api/v1/messages/{message_id}", headers=alice_headers)
    assert deleted.status_code == 200
    assert deleted.json()["is_deleted"] is True
    assert deleted.json()["content"] == ""


def test_cannot_send_empty_message(client: TestClient, db) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    headers = auth_headers(client, "alice")
    conversation_id = _conversation_id(client, headers, bob.id)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages", json={"content": "   "}, headers=headers
    )
    assert response.status_code == 422


def test_blocked_user_cannot_send_message(client: TestClient, db) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    alice_headers = auth_headers(client, "alice")
    bob_headers = auth_headers(client, "bob")
    conversation_id = _conversation_id(client, alice_headers, bob.id)

    client.post(f"/api/v1/users/{bob.id}/block", headers=alice_headers)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "can I still text?"},
        headers=bob_headers,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "blocked"


def test_message_to_conversation_you_are_not_part_of_is_404(client: TestClient, db) -> None:
    alice = make_user(db, username="alice")
    bob = make_user(db, username="bob")
    make_user(db, username="carol", password="Secret123")
    alice_headers = auth_headers(client, "alice")
    conversation_id = _conversation_id(client, alice_headers, bob.id)

    carol_headers = auth_headers(client, "carol")
    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "sneaky"},
        headers=carol_headers,
    )
    assert response.status_code == 404
