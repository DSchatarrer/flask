from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from src.core.manager_db import get_session, init_db
from src.core.models.sessions import Sessions
from src.core.models.users import Users
from src.core.session_cleanup import cleanup_expired_sessions


def test_session_context_rolls_back_on_exception(app):
    with app.app_context():
        with pytest.raises(RuntimeError):
            with get_session() as db:
                db.add(Users(usu="rollback", hash_pwd=None, role="user"))
                db.flush()
                raise RuntimeError("failure")
        with get_session() as db:
            assert db.get(Users, "rollback") is None


def test_cleanup_respects_retention(app):
    now = datetime.now(timezone.utc)
    with app.app_context():
        factory = app.extensions["session_factory"]
        with factory.begin() as db:
            db.add_all([
                Sessions(token="old", usu="admin", exp=now - timedelta(days=20)),
                Sessions(token="recent", usu="admin", exp=now - timedelta(days=1)),
                Sessions(token="permanent", usu="admin", exp=None),
            ])
        with factory.begin() as db:
            assert cleanup_expired_sessions(db, retention_days=7, now=now) == 1
        with factory() as db:
            assert set(db.scalars(select(Sessions.token)).all()) == {"recent", "permanent"}


def test_cleanup_rollback_does_not_delete(app):
    now = datetime.now(timezone.utc)
    with app.app_context():
        factory = app.extensions["session_factory"]
        with factory.begin() as db:
            db.add(Sessions(token="old", usu="admin", exp=now - timedelta(days=10)))
        with pytest.raises(ValueError):
            with factory.begin() as db:
                cleanup_expired_sessions(db, now=now)
                raise ValueError("rollback")
        with factory() as db:
            assert db.get(Sessions, "old") is not None


def test_cleanup_negative_retention_rejected(app):
    with app.app_context():
        with app.extensions["session_factory"]() as db:
            with pytest.raises(ValueError):
                cleanup_expired_sessions(db, retention_days=-1)


def test_existing_table_names_and_columns(app):
    from sqlalchemy import inspect
    inspector = inspect(app.extensions["sqlalchemy_engine"])
    assert {"usuarios", "sesiones"} <= set(inspector.get_table_names())
    assert {x["name"] for x in inspector.get_columns("usuarios")} == {"usu", "hash_pwd", "role"}
    assert {x["name"] for x in inspector.get_columns("sesiones")} == {"token", "usu", "exp"}
