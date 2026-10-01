"""Спільні фікстури: чиста тестова БД (Postgres, якщо TEST_DATABASE_URL заданий; інакше
файлова SQLite) на кожен тест, FastAPI TestClient та кілька готових користувачів."""

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get("TEST_DATABASE_URL", "sqlite:///./test_messenger.db"),
)
os.environ["ENVIRONMENT"] = "test"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ADMIN_USERNAME"] = ""
os.environ["ADMIN_EMAIL"] = ""
os.environ["ADMIN_PASSWORD"] = ""

from app.core.database import Base, engine  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, UserRole  # noqa: E402
from app.websocket.manager import manager  # noqa: E402

TestSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _clean_database() -> Iterator[None]:
    """Створює всі таблиці перед тестом і повністю очищує їх після — тести не бачать
    даних одне одного, а схема завжди узгоджена з поточними моделями (без Alembic)."""
    Base.metadata.create_all(engine)
    yield
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    limiter.reset()
    manager.reset()


@pytest.fixture
def db() -> Iterator[Session]:
    with TestSessionLocal() as session:
        yield session


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def make_user(
    db: Session,
    *,
    username: str = "alice",
    email: str | None = None,
    password: str = "Secret123",
    role: UserRole = UserRole.USER,
    display_name: str | None = None,
) -> User:
    user = User(
        username=username,
        email=email or f"{username}@example.com",
        password_hash=hash_password(password),
        display_name=display_name or username.capitalize(),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(client: TestClient, username: str, password: str = "Secret123") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"login": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_factory(db: Session):
    def _factory(**kwargs) -> User:
        return make_user(db, **kwargs)

    return _factory
