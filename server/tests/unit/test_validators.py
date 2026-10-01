"""Правила валідації username/email/password/повідомлень."""

import pytest

from app.schemas import validators as v


@pytest.mark.parametrize("value", ["bob", "bob_the_builder", "B0b_99", "abc"])
def test_check_username_accepts_valid(value: str) -> None:
    assert v.check_username(value) == value


@pytest.mark.parametrize("value", ["ab", "has space", "має-кирилицю", "x" * 33, "bad!name"])
def test_check_username_rejects_invalid(value: str) -> None:
    with pytest.raises(ValueError):
        v.check_username(value)


def test_check_email_normalizes_case() -> None:
    assert v.check_email("User@Example.COM") == "user@example.com"


def test_check_email_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        v.check_email("not-an-email")


@pytest.mark.parametrize("value", ["Secret123", "a1" * 10, "P@ssw0rd!"])
def test_check_password_accepts_valid(value: str) -> None:
    assert v.check_password(value) == value


@pytest.mark.parametrize("value", ["short1", "nodigitshere", "12345678", "x" * 129])
def test_check_password_rejects_invalid(value: str) -> None:
    with pytest.raises(ValueError):
        v.check_password(value)


def test_check_message_strips_and_rejects_empty() -> None:
    assert v.check_message("  hello  ") == "hello"
    with pytest.raises(ValueError):
        v.check_message("   ")


def test_check_message_rejects_too_long() -> None:
    with pytest.raises(ValueError):
        v.check_message("x" * 4001)
