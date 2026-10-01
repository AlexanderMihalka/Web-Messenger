"""/ws — автентифікація, presence (online/offline), message:new/edit/delete/read, typing.

TestClient веде REST- і WS-виклики через один event loop на весь `with TestClient(app)`,
тому push через anyio.from_thread.run з синхронних REST-роутерів долітає до WS-з'єднань,
відкритих тим самим клієнтом у цьому ж тесті — так само, як у реальному застосунку.
"""

from fastapi.testclient import TestClient

from tests.conftest import make_user


def _login(client: TestClient, username: str, password: str = "Secret123") -> tuple[str, int]:
    response = client.post("/api/v1/auth/login", json={"login": username, "password": password})
    body = response.json()
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    return body["access_token"], me.json()["id"]


def test_invalid_token_closes_connection(client: TestClient) -> None:
    from starlette.websockets import WebSocketDisconnect

    try:
        with client.websocket_connect("/ws?token=not-a-real-token") as ws:
            ws.receive_json()
        raise AssertionError("мало закритися до отримання даних")
    except WebSocketDisconnect as exc:
        assert exc.code == 4401


def test_connect_receives_ack(client: TestClient, db) -> None:
    make_user(db, username="alice", password="Secret123")
    token, user_id = _login(client, "alice")
    with client.websocket_connect(f"/ws?token={token}") as ws:
        ack = ws.receive_json()
        assert ack == {"type": "connection", "user_id": user_id, "server_time": ack["server_time"]}


def test_presence_online_and_offline_between_partners(client: TestClient, db) -> None:
    alice = make_user(db, username="alice", password="Secret123")
    bob = make_user(db, username="bob", password="Secret123")
    alice_token, _ = _login(client, "alice")
    bob_token, _ = _login(client, "bob")

    client.post(
        "/api/v1/conversations",
        json={"user_id": bob.id},
        headers={"Authorization": f"Bearer {alice_token}"},
    )

    with client.websocket_connect(f"/ws?token={alice_token}") as alice_ws:
        alice_ws.receive_json()  # connection ack
        with client.websocket_connect(f"/ws?token={bob_token}") as bob_ws:
            bob_ws.receive_json()  # connection ack
            assert alice_ws.receive_json() == {"type": "user:online", "user_id": bob.id}
        offline_evt = alice_ws.receive_json()
        assert offline_evt["type"] == "user:offline"
        assert offline_evt["user_id"] == bob.id


def test_new_conversation_notifies_already_online_partner(client: TestClient, db) -> None:
    alice = make_user(db, username="alice", password="Secret123")
    bob = make_user(db, username="bob", password="Secret123")
    alice_token, _ = _login(client, "alice")
    bob_token, _ = _login(client, "bob")

    with client.websocket_connect(f"/ws?token={alice_token}") as alice_ws:
        alice_ws.receive_json()
        with client.websocket_connect(f"/ws?token={bob_token}") as bob_ws:
            bob_ws.receive_json()
            client.post(
                "/api/v1/conversations",
                json={"user_id": bob.id},
                headers={"Authorization": f"Bearer {alice_token}"},
            )
            # обидва ще не знали одне про одного до створення діалогу — WS мав «дозвуковити»
            assert alice_ws.receive_json() == {"type": "user:online", "user_id": bob.id}
            assert bob_ws.receive_json() == {"type": "user:online", "user_id": alice.id}


def test_message_lifecycle_events_reach_recipient(client: TestClient, db) -> None:
    alice = make_user(db, username="alice", password="Secret123")
    bob = make_user(db, username="bob", password="Secret123")
    alice_token, _ = _login(client, "alice")
    bob_token, _ = _login(client, "bob")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}

    conversation_id = client.post(
        "/api/v1/conversations", json={"user_id": bob.id}, headers=alice_headers
    ).json()["id"]

    with client.websocket_connect(f"/ws?token={bob_token}") as bob_ws:
        bob_ws.receive_json()

        sent = client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "Привіт!"},
            headers=alice_headers,
        ).json()
        new_evt = bob_ws.receive_json()
        assert new_evt["type"] == "message:new"
        assert new_evt["message"]["content"] == "Привіт!"

        client.patch(
            f"/api/v1/messages/{sent['id']}", json={"content": "Привіт, Бобе!"}, headers=alice_headers
        )
        edit_evt = bob_ws.receive_json()
        assert edit_evt["type"] == "message:edit"
        assert edit_evt["message"]["content"] == "Привіт, Бобе!"

        client.delete(f"/api/v1/messages/{sent['id']}", headers=alice_headers)
        delete_evt = bob_ws.receive_json()
        assert delete_evt == {
            "type": "message:delete",
            "conversation_id": conversation_id,
            "message_id": sent["id"],
        }


def test_read_receipt_event_reaches_sender(client: TestClient, db) -> None:
    alice = make_user(db, username="alice", password="Secret123")
    bob = make_user(db, username="bob", password="Secret123")
    alice_token, _ = _login(client, "alice")
    bob_token, bob_id = _login(client, "bob")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}

    conversation_id = client.post(
        "/api/v1/conversations", json={"user_id": bob.id}, headers=alice_headers
    ).json()["id"]
    message_id = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "hi"},
        headers=alice_headers,
    ).json()["id"]

    with client.websocket_connect(f"/ws?token={alice_token}") as alice_ws:
        alice_ws.receive_json()
        client.post(
            f"/api/v1/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {bob_token}"},
        )
        read_evt = alice_ws.receive_json()
        assert read_evt == {
            "type": "message:read",
            "conversation_id": conversation_id,
            "user_id": bob_id,
            "last_read_message_id": message_id,
        }


def test_typing_indicator_relayed_to_partner_only(client: TestClient, db) -> None:
    alice = make_user(db, username="alice", password="Secret123")
    bob = make_user(db, username="bob", password="Secret123")
    alice_token, alice_id = _login(client, "alice")
    bob_token, _ = _login(client, "bob")
    alice_headers = {"Authorization": f"Bearer {alice_token}"}

    conversation_id = client.post(
        "/api/v1/conversations", json={"user_id": bob.id}, headers=alice_headers
    ).json()["id"]

    with client.websocket_connect(f"/ws?token={alice_token}") as alice_ws:
        alice_ws.receive_json()
        with client.websocket_connect(f"/ws?token={bob_token}") as bob_ws:
            bob_ws.receive_json()
            alice_ws.send_json({"type": "typing:start", "conversation_id": conversation_id})
            evt = bob_ws.receive_json()
            assert evt == {
                "type": "typing:start",
                "conversation_id": conversation_id,
                "user_id": alice_id,
            }


def test_ping_pong(client: TestClient, db) -> None:
    make_user(db, username="alice", password="Secret123")
    token, _ = _login(client, "alice")
    with client.websocket_connect(f"/ws?token={token}") as ws:
        ws.receive_json()
        ws.send_json({"type": "ping"})
        assert ws.receive_json() == {"type": "pong"}
