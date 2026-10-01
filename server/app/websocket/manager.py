"""Реєстр активних WebSocket-зʼєднань. Один користувач = один запис ключа,
але може мати кілька живих сокетів (кілька вкладок/пристроїв одночасно)."""

import asyncio
import logging

from starlette.websockets import WebSocket

logger = logging.getLogger("messenger.ws")


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> bool:
        """Реєструє сокет. Повертає True, якщо це перше зʼєднання користувача (став online)."""
        async with self._lock:
            was_offline = not self._connections.get(user_id)
            self._connections.setdefault(user_id, set()).add(websocket)
            return was_offline

    async def disconnect(self, user_id: int, websocket: WebSocket) -> bool:
        """Знімає сокет з реєстру. Повертає True, якщо це було останнє зʼєднання (став offline)."""
        async with self._lock:
            conns = self._connections.get(user_id)
            if not conns or websocket not in conns:
                return False
            conns.discard(websocket)
            if not conns:
                self._connections.pop(user_id, None)
                return True
            return False

    def is_online(self, user_id: int) -> bool:
        return bool(self._connections.get(user_id))

    def online_subset(self, user_ids: set[int]) -> set[int]:
        return {uid for uid in user_ids if self._connections.get(uid)}

    async def send_to_user(self, user_id: int, payload: dict) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(user_id, ())):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(user_id, ws)

    async def send_to_users(self, user_ids: set[int] | list[int], payload: dict) -> None:
        for uid in set(user_ids):
            await self.send_to_user(uid, payload)

    def connection_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())

    def online_user_count(self) -> int:
        return len(self._connections)

    def reset(self) -> None:
        """Лише для тестів: скидає реєстр між тестовими прогонами."""
        self._connections.clear()


manager = ConnectionManager()
