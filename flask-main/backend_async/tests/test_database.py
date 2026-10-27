from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import inspect, select
from src.core.manager_db import get_session
from src.core.models.sessions import Sessions
from src.core.models.users import Users
from src.core.session_cleanup import cleanup_expired_sessions
from tests.conftest import run_async


def test_session_context_rolls_back_on_exception(app):
    async def check():
        with pytest.raises(RuntimeError):
            async with get_session() as db:
                db.add(Users(usu="rollback", hash_pwd=None, role="user"))
                await db.flush()
                raise RuntimeError("failure")
        async with get_session() as db:
            assert await db.get(Users, "rollback") is None
    with app.app_context():
        run_async(check())


def test_cleanup_respects_retention(app):
    async def check():
        now = datetime.now(timezone.utc)
        factory = app.extensions["session_factory"]
        async with factory.begin() as db:
            db.add_all([
                Sessions(token="old", usu="admin", exp=now - timedelta(days=20)),
                Sessions(token="recent", usu="admin", exp=now - timedelta(days=1)),
                Sessions(token="permanent", usu="admin", exp=None),
            ])
        async with factory.begin() as db:
            assert await cleanup_expired_sessions(db, retention_days=7, now=now) == 1
        async with factory() as db:
            assert set((await db.scalars(select(Sessions.token))).all()) == {"recent", "permanent"}
    with app.app_context():
        run_async(check())


def test_cleanup_rollback_does_not_delete(app):
    async def check():
        now = datetime.now(timezone.utc)
        factory = app.extensions["session_factory"]
        async with factory.begin() as db:
            db.add(Sessions(token="old", usu="admin", exp=now - timedelta(days=10)))
        with pytest.raises(ValueError):
            async with factory.begin() as db:
                await cleanup_expired_sessions(db, now=now)
                raise ValueError("rollback")
        async with factory() as db:
            assert await db.get(Sessions, "old") is not None
    with app.app_context():
        run_async(check())


def test_cleanup_negative_retention_rejected(app):
    async def check():
        async with app.extensions["session_factory"]() as db:
            with pytest.raises(ValueError):
                await cleanup_expired_sessions(db, retention_days=-1)
    with app.app_context():
        run_async(check())


def test_existing_table_names_and_columns(app):
    def verify(connection):
        inspector = inspect(connection)
        assert {"usuarios", "sesiones"} <= set(inspector.get_table_names())
        assert {x["name"] for x in inspector.get_columns("usuarios")} == {"usu", "hash_pwd", "role"}
        assert {x["name"] for x in inspector.get_columns("sesiones")} == {"token", "usu", "exp"}
    async def check():
        async with app.extensions["sqlalchemy_engine"].connect() as connection:
            await connection.run_sync(verify)
    with app.app_context():
        run_async(check())
