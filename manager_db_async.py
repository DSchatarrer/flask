# core/async_manager_db.py
from contextlib import asynccontextmanager
from functools import wraps
from typing import AsyncGenerator

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker, AsyncSession
)

DATABASE_URL = (
    "postgresql+asyncpg://dxxxxxx01achackia05-postgresql.postgres.database.azure.com:5432/postgres"
)

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
)

async_session_maker = async_sessionmaker(
    bind=async_engine, expire_on_commit=False
)

# ----------  inicialización ----------
async def init_db() -> None:
    async with async_engine.begin() as conn:
        # importa aquí tus modelos
        from src.models.models import Model
        await conn.run_sync(SQLModel.metadata.create_all)

# ----------  generador de sesión ----------
@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:  # igual que Depends
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# ----------  decorador estilo FastAPI ----------
def require_async_db_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with async_session_maker() as db:
            kwargs["db"] = db
            return await func(*args, **kwargs)
    return wrapper










# routes/models_routes_async.py
from flask.views import MethodView
from flask_smorest import Blueprint

from src.core.async_manager_db import require_async_db_session
from src.services.model_service import DemoDataService

blp = Blueprint(
    "models_async", "models_async",
    url_prefix="/models",
    description="Operaciones con modelos (async)"
)

@blp.route("/demo-data")
class DemoDataList(MethodView):
    @blp.response(200)
    @require_async_db_session
    async def get(self, db):
        # ¡Ojo! DemoDataService debe exponer métodos async
        data = await DemoDataService(db).get_all_demo_data()
        return data
