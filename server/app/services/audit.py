"""Запис подій у журнал: одночасно в stdout (docker logs / journalctl) і в таблицю
audit_logs, яку показує GET /api/v1/admin/logs. Один виклик — обидва місця призначення,
щоб рядок логів і рядок у БД ніколи не розходилися."""

import logging

from sqlalchemy.orm import Session

from app.models import AuditLog

_logger = logging.getLogger("messenger.audit")
_LEVEL_METHOD = {"INFO": _logger.info, "WARNING": _logger.warning, "ERROR": _logger.error}


def record(
    db: Session,
    *,
    event: str,
    level: str = "INFO",
    actor_id: int | None = None,
    ip_address: str | None = None,
    message: str = "",
) -> None:
    log_fn = _LEVEL_METHOD.get(level.upper(), _logger.info)
    log_fn("%s actor_id=%s ip=%s %s", event, actor_id, ip_address, message)
    db.add(
        AuditLog(
            level=level.upper(),
            event=event,
            actor_id=actor_id,
            ip_address=ip_address,
            message=message,
        )
    )
