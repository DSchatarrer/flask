import pytest
from werkzeug.security import generate_password_hash

from src.core.manager_db import init_db
from src.core.models.users import Users
from src.core.settings import Settings
from src.main import create_app


@pytest.fixture
def app(tmp_path):
    settings = Settings(
        _env_file=None,
        FLASK_SECRET_KEY="test-flask-secret-is-at-least-32-chars",
        JWT_SECRET_KEY="test-jwt-secret-is-at-least-32-chars",
        API_KEY="test-api-key",
        DATABASE_URL=f"sqlite+pysqlite:///{tmp_path / 'test.sqlite'}",
        COOKIE_SECURE=False,
    )
    app = create_app(settings=settings, test_config={"TESTING": True})
    with app.app_context():
        init_db()
        with app.extensions["session_factory"].begin() as db:
            db.add_all([
                Users(usu="admin", hash_pwd=generate_password_hash("supersecret"), role="admin"),
                Users(usu="worker", hash_pwd=generate_password_hash("workerpass"), role="user"),
            ])
    yield app
    app.extensions["sqlalchemy_engine"].dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username="admin", password="supersecret"):
    return client.post("/login/", json={"user": username, "password": password})
