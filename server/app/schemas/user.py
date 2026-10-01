from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator

from app.schemas import validators as v


class UserPublic(BaseModel):
    id: int
    username: str
    display_name: str
    avatar_url: str | None = None
    bio: str | None = None
    is_online: bool = False
    last_seen_at: datetime | None = None
    created_at: datetime


class UserMe(UserPublic):
    email: str
    role: str
    is_blocked: bool = False


class UserUpdate(BaseModel):
    """PATCH /users/me: змінюються лише передані поля."""

    display_name: str | None = None
    username: str | None = None
    bio: str | None = None

    @field_validator("username")
    @classmethod
    def _username(cls, value: str | None) -> str | None:
        return None if value is None else v.check_username(value)

    @field_validator("display_name")
    @classmethod
    def _display_name(cls, value: str | None) -> str | None:
        return None if value is None else v.check_display_name(value)

    @field_validator("bio")
    @classmethod
    def _bio(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 500:
            raise ValueError("Опис занадто довгий (максимум 500 символів)")
        return value or None

    def provided(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.model_fields_set}
