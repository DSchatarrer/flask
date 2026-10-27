"""Esquema y contrato async verificables sin Flask o controladores DB externos."""
import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.dialects import sqlite, postgresql, mysql
from sqlalchemy.schema import CreateTable

from src.core.models import Base
from src.core.session_cleanup import cleanup_expired_sessions


def test_original_schema_stays_identical():
    assert set(Base.metadata.tables) == {"usuarios", "sesiones"}
    assert list(Base.metadata.tables["usuarios"].columns.keys()) == ["usu", "hash_pwd", "role"]
    assert list(Base.metadata.tables["sesiones"].columns.keys()) == ["token", "usu", "exp"]


def test_ddl_compiles_for_three_engines():
    for dialect in [sqlite.dialect(), postgresql.dialect(), mysql.dialect()]:
        ddl = [str(CreateTable(table).compile(dialect=dialect)) for table in Base.metadata.tables.values()]
        assert all("CREATE TABLE" in sql for sql in ddl)


def test_cleanup_executes_async_delete_with_expected_cutoff():
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(rowcount=2)))
    now = datetime(2026, 10, 27, tzinfo=timezone.utc)
    assert asyncio.run(cleanup_expired_sessions(db, retention_days=7, now=now)) == 2
    sql = db.execute.await_args.args[0]
    assert sql.is_delete
    compiled = sql.compile(dialect=sqlite.dialect())
    assert datetime(2026, 10, 20, tzinfo=timezone.utc) in compiled.params.values()


def test_invalid_retention():
    db = SimpleNamespace(execute=AsyncMock())
    with pytest.raises(ValueError):
        asyncio.run(cleanup_expired_sessions(db, retention_days=-1))
    db.execute.assert_not_awaited()


def test_timezone_required():
    db = SimpleNamespace(execute=AsyncMock())
    with pytest.raises(ValueError):
        asyncio.run(cleanup_expired_sessions(db, now=datetime(2026, 10, 27)))
    db.execute.assert_not_awaited()
