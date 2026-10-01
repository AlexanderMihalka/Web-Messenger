"""Профіль, пошук, список користувачів, блокування."""

from sqlalchemy.orm import Session

from app.models import User
from app.repositories.block_repository import BlockRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import Page
from app.schemas.user import UserMe, UserPublic, UserUpdate
from app.services import audit
from app.services.exceptions import Conflict, NotFound
from app.services.mappers import to_user_me, to_user_public


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.blocks = BlockRepository(db)

    def get_public(self, target_id: int) -> UserPublic:
        user = self.users.get(target_id)
        if user is None:
            raise NotFound("Користувача не знайдено")
        return to_user_public(user)

    def search(self, actor_id: int, query: str) -> list[UserPublic]:
        query = query.strip()
        if len(query) < 1:
            return []
        hidden = self._hidden_ids(actor_id)
        rows = self.users.search(query, exclude_id=actor_id, hidden_ids=hidden)
        return [to_user_public(u) for u in rows]

    def list_public(self, actor_id: int, limit: int, offset: int) -> Page[UserPublic]:
        hidden = self._hidden_ids(actor_id)
        rows, total = self.users.list_public(actor_id, hidden, limit, offset)
        return Page(items=[to_user_public(u) for u in rows], total=total, limit=limit, offset=offset)

    def _hidden_ids(self, actor_id: int) -> set[int]:
        """Кого не показувати в загальному списку/пошуку: кого сам заблокував і хто
        заблокував тебе — двосторонньо, щоб не наштовхуватись одне на одного випадково."""
        blocked_by_me, blocked_me = self.blocks.related_ids(actor_id)
        return blocked_by_me | blocked_me

    def update_me(self, user: User, data: UserUpdate) -> UserMe:
        fields = data.provided()
        if "username" in fields and fields["username"] is not None:
            new_username = fields["username"].lower()
            if new_username != user.username:
                existing = self.users.get_by_username(new_username)
                if existing is not None and existing.id != user.id:
                    raise Conflict("Це імʼя користувача вже зайняте")
                user.username = new_username
        if "display_name" in fields and fields["display_name"] is not None:
            user.display_name = fields["display_name"]
        if "bio" in fields:
            user.bio = fields["bio"]
        self.db.commit()
        self.db.refresh(user)
        return to_user_me(user)

    def set_avatar_url(self, user: User, avatar_url: str) -> UserMe:
        user.avatar_url = avatar_url
        self.db.commit()
        self.db.refresh(user)
        return to_user_me(user)

    def block(self, actor: User, target_id: int) -> None:
        if target_id == actor.id:
            raise Conflict("Не можна заблокувати самого себе")
        target = self.users.get(target_id)
        if target is None:
            raise NotFound("Користувача не знайдено")
        if self.blocks.get(actor.id, target_id) is None:
            self.blocks.add(actor.id, target_id)
            audit.record(
                self.db, event="user_block", actor_id=actor.id, message=f"target_id={target_id}"
            )
            self.db.commit()

    def unblock(self, actor: User, target_id: int) -> None:
        existing = self.blocks.get(actor.id, target_id)
        if existing is not None:
            self.blocks.remove(existing)
            audit.record(
                self.db, event="user_unblock", actor_id=actor.id, message=f"target_id={target_id}"
            )
            self.db.commit()

    def list_blocked(self, actor: User) -> list[UserPublic]:
        return [to_user_public(u) for u in self.blocks.blocked_users(actor.id)]
