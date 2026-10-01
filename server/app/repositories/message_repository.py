from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Message


class MessageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, message_id: int) -> Message | None:
        return self.db.get(Message, message_id)

    def add(self, message: Message) -> Message:
        self.db.add(message)
        self.db.flush()
        return message

    def page(
        self, conversation_id: int, after_id: int, before_id: int | None, limit: int
    ) -> tuple[list[Message], bool]:
        """Сторінка історії, завжди повертається в хронологічному порядку. Напрямок вибірки
        залежить від того, які межі задані — це дві різні дії з погляду користувача:

        - `before_id` задано (гортання вгору, до старіших) — беремо `limit` повідомлень,
          що йдуть ОДРАЗУ ПЕРЕД цією межею (найближчі до неї), тобто сортуємо за id DESC
          і розвертаємо назад у хронологічний порядок.
        - лише `after_id` > 0 задано, без `before_id` (\"наздогнати\" пропущене після
          реконекту) — беремо `limit` повідомлень ОДРАЗУ ПІСЛЯ цієї межі, сортуємо за id ASC.
        - жодної межі немає (перше відкриття діалогу) — це той самий випадок, що й гортання
          вгору від «кінця»: беремо `limit` найновіших повідомлень.

        Без цього розгалуження `after_id=0` без `before_id` повертав би найновіші `limit`
        повідомлень з усього діалогу, а не найстаріші — не той результат при спробі прогорнути
        історію вперед від конкретної точки.
        """
        stmt = select(Message).where(
            Message.conversation_id == conversation_id, Message.id > after_id
        )
        if before_id is not None:
            stmt = stmt.where(Message.id < before_id)

        if before_id is None and after_id > 0:
            # Вперед від конкретної точки: найстаріші з нових — уже в хронологічному порядку.
            rows = list(self.db.scalars(stmt.order_by(Message.id.asc()).limit(limit + 1)))
            has_more = len(rows) > limit
            return rows[:limit], has_more

        # Початкове відкриття діалогу або гортання вгору: найновіші в межах вікна,
        # тоді розвертаємо назад у хронологічний порядок для відображення.
        rows = list(self.db.scalars(stmt.order_by(Message.id.desc()).limit(limit + 1)))
        has_more = len(rows) > limit
        rows = rows[:limit]
        rows.reverse()
        return rows, has_more

    def max_id(self, conversation_id: int) -> int:
        value = self.db.scalar(
            select(func.max(Message.id)).where(Message.conversation_id == conversation_id)
        )
        return value or 0
