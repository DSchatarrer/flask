# core/manager_db.py

import os
from functools import wraps
from sqlmodel import SQLModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


# DATABASE_URL = "postgresql+psycopg2://iber:iber@localhost:5432/iberdrola_dev"
DATABASE_URL = "postgresql+psycopg2://xxxx:xxxx@xxxxx-postgresql.postgres.database.azure.com:5432/postgres"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30
)

SessionLocal = sessionmaker(bind=engine)

def init_db() -> None:
    """Crear las tablas y vistas"""
    try:
        from src.models.models import Model
    except:
        from models.models import Model

    # from bbdd.ddl import create_view_ddl, create_view_ddl_itnow

    SQLModel.metadata.create_all(engine)

    # with engine.connect() as conn:
    #     conn.execute(create_view_ddl)
    #     conn.execute(create_view_ddl_itnow)

def get_session() -> Session:
    """Devuelve una sesión de base de datos"""
    return SessionLocal()

def require_db_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        db = get_session()
        try:
            return func(*args, db=db, **kwargs)
        finally:
            db.close()
    return wrapper



# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, Session
# from functools import wraps
# from src.core.token_manager import TokenManager

# token_manager = TokenManager()

# SessionLocal = None
# _engine = None  # guarda el engine actual
# _current_token = None  # guarda el token asociado a ese engine


# def init_db():
#     global SessionLocal, _engine, _current_token
#     token = token_manager.get_token()
#     _current_token = token

#     _engine = create_engine(f"postgresql://user:{token}@host:5432/dbname")
#     SessionLocal = sessionmaker(bind=_engine)


# def get_session() -> Session:
#     """Devuelve una sesión de base de datos (regenera engine si el token ha caducado)"""
#     global SessionLocal, _engine, _current_token

#     token = token_manager.get_token()

#     if token != _current_token:
#         # El token ha cambiado, así que regeneramos engine y sessionmaker
#         _engine.dispose()  # Cierra conexiones activas
#         _engine = create_engine(f"postgresql://user:{token}@host:5432/dbname")
#         SessionLocal = sessionmaker(bind=_engine)
#         _current_token = token

#     return SessionLocal()


# def require_db_session(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         db = get_session()
#         try:
#             return func(*args, db=db, **kwargs)
#         finally:
#             db.close()
#     return wrapper