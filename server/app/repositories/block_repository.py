from sqlalchemy import and_, delete, or_, select
from sqlalchemy.orm import Session

from app.models import Block, User


class BlockRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, blocker_id: int, blocked_id: int) -> Block | None:
        return self.db.scalar(
            select(Block).where(Block.blocker_id == blocker_id, Block.blocked_id == blocked_id)
        )

    def exists_between(self, a: int, b: int) -> bool:
        stmt = (
            select(Block.id)
            .where(
                or_(
                    and_(Block.blocker_id == a, Block.blocked_id == b),
                    and_(Block.blocker_id == b, Block.blocked_id == a),
                )
            )
            .limit(1)
        )
        return self.db.scalar(stmt) is not None

    def add(self, blocker_id: int, blocked_id: int) -> Block:
        block = Block(blocker_id=blocker_id, blocked_id=blocked_id)
        self.db.add(block)
        self.db.flush()
        return block

    def remove(self, block: Block) -> None:
        self.db.delete(block)
        self.db.flush()

    def blocked_users(self, blocker_id: int) -> list[User]:
        stmt = (
            select(User)
            .join(Block, Block.blocked_id == User.id)
            .where(Block.blocker_id == blocker_id)
            .order_by(Block.created_at.desc(), Block.id.desc())
        )
        return list(self.db.scalars(stmt))

    def related_ids(self, user_id: int) -> tuple[set[int], set[int]]:
        """(кого заблокував користувач, хто заблокував користувача)."""
        rows = self.db.execute(
            select(Block.blocker_id, Block.blocked_id).where(
                or_(Block.blocker_id == user_id, Block.blocked_id == user_id)
            )
        ).all()
        by_me = {blocked for blocker, blocked in rows if blocker == user_id}
        me_blocked = {blocker for blocker, blocked in rows if blocked == user_id}
        return by_me, me_blocked

    def delete_for_user(self, user_id: int) -> None:
        self.db.execute(
            delete(Block).where(or_(Block.blocker_id == user_id, Block.blocked_id == user_id))
        )
