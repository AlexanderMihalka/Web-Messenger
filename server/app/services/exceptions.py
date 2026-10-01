"""Внутрішні винятки сервісного шару (не привʼязані до HTTP)."""


class ServiceError(Exception):
    pass


class NotFound(ServiceError):
    pass


class Conflict(ServiceError):
    pass


class Forbidden(ServiceError):
    pass


class Blocked(ServiceError):
    """Дія неможлива через блокування (в один або інший бік)."""
