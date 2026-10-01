"""Конфігурація застосунку зі змінних середовища / .env."""

from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET = "change-me-in-production-please-use-a-long-random-string"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Messenger Web"
    environment: str = "development"  # development | test | production
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://messenger:messenger@localhost:5432/messenger"

    secret_key: str = DEFAULT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    rate_limit_enabled: bool = True
    rate_limit_general_per_minute: int = 300
    rate_limit_auth_per_minute: int = 10

    upload_dir: str = "uploads"
    max_avatar_bytes: int = 2 * 1024 * 1024

    admin_username: str | None = None
    admin_email: str | None = None
    admin_password: str | None = None

    @field_validator("admin_username", "admin_email", "admin_password", mode="before")
    @classmethod
    def _empty_to_none(cls, value: object) -> object:
        return None if value == "" else value

    @model_validator(mode="after")
    def _check_secret(self) -> "Settings":
        if self.environment == "production" and (
            self.secret_key == DEFAULT_SECRET or len(self.secret_key) < 32
        ):
            raise ValueError("SECRET_KEY має бути унікальним і містити щонайменше 32 символи")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
