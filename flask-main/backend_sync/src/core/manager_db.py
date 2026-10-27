"""Un Engine/SessionFactory por aplicación; una Session por operación HTTP/CLI."""
from contextlib import contextmanager
from functools import wraps
from collections.abc import Generator

from flask import Flask, current_app
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.models.base import Base


def configure_database(app: Flask) -> None:
    engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"], pool_pre_ping=True, pool_recycle=1800)
    factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    app.extensions["sqlalchemy_engine"] = engine
    app.extensions["session_factory"] = factory


def get_session_factory() -> sessionmaker[Session]:
    return current_app.extensions["session_factory"]


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Para servicios y tareas CLI, cierra al salir y revierte al fallar."""
    with get_session_factory()() as db:
        try:
            yield db
        except BaseException:
            db.rollback()
            raise


def require_db_session(view_func):
    """Inyecta db sin crear sessionmaker por petición. No hace commits implícitos."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        with get_session() as db:
            return view_func(*args, db=db, **kwargs)
    return wrapper


def init_db() -> None:
    """Solo desarrollo/primer despliegue. Producción: migraciones Alembic."""
    import src.core.models  # noqa: F401
    engine: Engine = current_app.extensions["sqlalchemy_engine"]
    Base.metadata.create_all(engine)
