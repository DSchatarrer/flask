"""Un AsyncEngine/async_sessionmaker por aplicación; una AsyncSession por operación."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import wraps

from flask import Flask, current_app
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.core.models.base import Base


def configure_database(app: Flask) -> None:
    # NullPool evita reutilizar conexiones entre loops WSGI, CLI y tests.
    # En un despliegue ASGI exclusivo se puede evaluar un pool persistente.
    engine = create_async_engine(
        app.config["SQLALCHEMY_DATABASE_URI"],
        pool_pre_ping=True,
        pool_recycle=1800,
        poolclass=NullPool,
    )
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    app.extensions["sqlalchemy_engine"] = engine
    app.extensions["session_factory"] = factory


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return current_app.extensions["session_factory"]


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Sin commit implícito. Reversión explícita y cierre garantizado."""
    factory = get_session_factory()
    async with factory() as db:
        try:
            yield db
        except BaseException:
            await db.rollback()
            raise


def require_db_session(view_func):
    """Inyecta AsyncSession en cada petición. Debe preceder a @require_auth."""
    @wraps(view_func)
    async def wrapper(*args, **kwargs):
        async with get_session() as db:
            return await view_func(*args, db=db, **kwargs)
    return wrapper


async def init_db() -> None:
    """Solo BD nueva en desarrollo. Producción: Alembic."""
    import src.core.models  # noqa: F401
    engine: AsyncEngine = current_app.extensions["sqlalchemy_engine"]
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def dispose_database(app: Flask) -> None:
    """Cerrar el pool al apagar la aplicación/proceso, no en cada request."""
    await app.extensions["sqlalchemy_engine"].dispose()
