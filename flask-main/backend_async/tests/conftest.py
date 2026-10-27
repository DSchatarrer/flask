"""Fixtures SQLite aiosqlite con Engine aislado por test."""
import asyncio

import pytest
from werkzeug.security import generate_password_hash

from src.core.manager_db import init_db, dispose_database
from src.core.models.users import Users
from src.core.settings import Settings
from src.main import create_app


def run_async(coro):
    """Solo desde tests/CLI síncronos; no utilizar dentro de vistas async."""
    return asyncio.run(coro)


@pytest.fixture
def app(tmp_path):
    settings = Settings(
        _env_file=None,
        FLASK_SECRET_KEY="test-flask-secret-is-at-least-32-chars",
        JWT_SECRET_KEY="test-jwt-secret-is-at-least-32-chars",
        API_KEY="test-api-key",
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'test.sqlite'}",
        COOKIE_SECURE=False,
    )
    app = create_app(settings=settings, test_config={"TESTING": True})
    async def setup():
        await init_db()
        factory = app.extensions["session_factory"]
        async with factory.begin() as db:
            db.add_all([
                Users(usu="admin", hash_pwd=generate_password_hash("supersecret"), role="admin"),
                Users(usu="worker", hash_pwd=generate_password_hash("workerpass"), role="user"),
            ])
    with app.app_context():
        run_async(setup())
    yield app
    run_async(dispose_database(app))


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username="admin", password="supersecret"):
    return client.post("/login/", json={"user": username, "password": password})
