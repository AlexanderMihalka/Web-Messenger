from pydantic import BaseModel, ValidationInfo, field_validator

from app.schemas import validators as v


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str
    display_name: str | None = None

    @field_validator("username")
    @classmethod
    def _username(cls, value: str) -> str:
        return v.check_username(value)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return v.check_email(value)

    @field_validator("password")
    @classmethod
    def _password(cls, value: str) -> str:
        return v.check_password(value)

    @field_validator("confirm_password")
    @classmethod
    def _confirm(cls, value: str, info: ValidationInfo) -> str:
        password = info.data.get("password")
        if password is not None and value != password:
            raise ValueError("Паролі не збігаються")
        return value

    @field_validator("display_name")
    @classmethod
    def _display_name(cls, value: str | None) -> str | None:
        return None if value is None or not value.strip() else v.check_display_name(value)


class LoginRequest(BaseModel):
    login: str  # username або email
    password: str


class RefreshRequest(BaseModel):
    """Тіло не обов'язкове: основний шлях — httpOnly cookie `refresh_token`.
    Поле-запасний варіант лишається для Swagger UI, тестів та не-браузерних клієнтів."""

    refresh_token: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
