"""Drivers aiosqlite/asyncpg y URL seguras sin iniciar Flask."""
import pytest
from sqlalchemy.engine import make_url

from src.core.settings import Settings


DEFAULTS = dict(
    _env_file=None,
    FLASK_SECRET_KEY="test-flask-secret-is-at-least-32-chars",
    JWT_SECRET_KEY="test-jwt-secret-is-at-least-32-chars",
    API_KEY="test-key",
)


@pytest.mark.parametrize("old, expected", [
    ("sqlite+pysqlite:///file.sqlite", "sqlite+aiosqlite"),
    ("sqlite+aiosqlite:///file.sqlite", "sqlite+aiosqlite"),
    ("postgresql+psycopg2://admin:pass@localhost/test", "postgresql+asyncpg"),
    ("postgresql+asyncpg://admin:pass@localhost/test", "postgresql+asyncpg"),
])
def test_driver_remapping(old, expected):
    cfg = Settings(**DEFAULTS, DATABASE_URL=old)
    assert make_url(cfg.sqlalchemy_database_uri).drivername == expected


def test_unsupported_driver_rejected():
    cfg = Settings(**DEFAULTS, DATABASE_URL="mysql+pymysql://root:pass@localhost/test")
    with pytest.raises(ValueError, match="Driver asíncrono"):
        _ = cfg.sqlalchemy_database_uri


def test_datasource_connection_escapes_password_correctly():
    cfg = Settings(
        **DEFAULTS,
        DATASOURCE_DB="db", DATASOURCE_FQDN="localhost", DATASOURCE_USR="user",
        DATASOURCE_PWD="p@ss:w/rd", DATASOURCE_PORT=5432,
    )
    url = make_url(cfg.sqlalchemy_database_uri)
    assert url.drivername == "postgresql+asyncpg"
    assert url.password == "p@ss:w/rd"
