"""Спільні правила валідації (повідомлення українською — їх бачить користувач у формі)."""

import re

from email_validator import EmailNotValidError, validate_email

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")
USERNAME_HINT = "Username: 3–32 символи, лише латиниця, цифри та підкреслення"
MESSAGE_MAX_LENGTH = 4000


def check_username(value: str) -> str:
    value = value.strip()
    if not USERNAME_RE.fullmatch(value):
        raise ValueError(USERNAME_HINT)
    return value


def check_email(value: str) -> str:
    try:
        return validate_email(value.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError as exc:
        raise ValueError("Некоректний формат email") from exc


def check_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Пароль має містити щонайменше 8 символів")
    if len(value) > 128:
        raise ValueError("Пароль занадто довгий (максимум 128 символів)")
    if not any(ch.isalpha() for ch in value):
        raise ValueError("Пароль має містити хоча б одну літеру")
    if not any(ch.isdigit() for ch in value):
        raise ValueError("Пароль має містити хоча б одну цифру")
    return value


def check_display_name(value: str) -> str:
    value = " ".join(value.split())
    if not 1 <= len(value) <= 64:
        raise ValueError("Імʼя має містити від 1 до 64 символів")
    return value


def check_message(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Повідомлення не може бути порожнім")
    if len(value) > MESSAGE_MAX_LENGTH:
        raise ValueError(f"Повідомлення занадто довге (максимум {MESSAGE_MAX_LENGTH} символів)")
    return value
