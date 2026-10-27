"""Ejecutables sin Flask: portabilidad, modelos y limpieza por SQLAlchemy."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.dialects import sqlite, postgresql, mysql
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

from src.core.models import Base, Users, Sessions
from src.core.session_cleanup import cleanup_expired_sessions


def test_original_schema_stays_identical():
    assert set(Base.metadata.tables) == {"usuarios", "sesiones"}
    assert list(Base.metadata.tables["usuarios"].columns.keys()) == ["usu", "hash_pwd", "role"]
    assert list(Base.metadata.tables["sesiones"].columns.keys()) == ["token", "usu", "exp"]


def test_ddl_compiles_for_three_engines():
    for dialect in [sqlite.dialect(), postgresql.dialect(), mysql.dialect()]:
        ddl = [str(CreateTable(table).compile(dialect=dialect)) for table in Base.metadata.tables.values()]
        assert all("CREATE TABLE" in sql for sql in ddl)


def test_expired_cleanup_respects_retention_and_no_implicit_commit():
    eng = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(eng)
    now = datetime.now(timezone.utc)
    with Session(eng) as s, s.begin():
        s.add(Users(usu="a", hash_pwd=None, role="admin"))
        s.add_all([
            Sessions(token="old", usu="a", exp=now - timedelta(days=20)),
            Sessions(token="recent", usu="a", exp=now - timedelta(days=1)),
            Sessions(token="none", usu="a", exp=None),
        ])
    with Session(eng) as s, s.begin():
        assert cleanup_expired_sessions(s, retention_days=7, now=now) == 1
    with Session(eng) as s:
        assert set(s.scalars(select(Sessions.token))) == {"recent", "none"}
    eng.dispose()


def test_cleanup_rollback():
    eng = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(eng)
    now = datetime.now(timezone.utc)
    with Session(eng) as s, s.begin():
        s.add(Sessions(token="rollback", usu="a", exp=now - timedelta(days=20)))
    with pytest.raises(RuntimeError):
        with Session(eng) as s, s.begin():
            cleanup_expired_sessions(s, now=now)
            raise RuntimeError()
    with Session(eng) as s:
        assert s.get(Sessions, "rollback") is not None
    eng.dispose()


def test_invalid_retention():
    eng = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(eng)
    with Session(eng) as s, pytest.raises(ValueError):
        cleanup_expired_sessions(s, retention_days=-1)
    eng.dispose()
