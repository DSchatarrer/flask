# core/manager_db_sync.py
from functools import wraps
from typing import Generator

from sqlmodel import SQLModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = (
    "postgresql+psycopg2://dxxxxxx01achackia05-postgresql.postgres.database.azure.com:5432/postgres"
)

# ----------  motor y pool ----------
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,   # reciclar conexiones tras 30′
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
)

SessionLocal = sessionmaker(bind=engine)

# ----------  inicializar tablas ----------
def init_db() -> None:
    """
    Crea las tablas (y vistas si las añades aquí).
    Llama a esta función una sola vez al iniciar la app (p. ej.  en create_app()).
    """
    # importa aquí tus modelos
    from src.models.models import Model
    SQLModel.metadata.create_all(engine)

# ----------  generador tipo Depends ----------
def get_session() -> Generator[Session, None, None]:
    """
    Abre una sesión, la cede al caller y la cierra al salir.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------  decorador “require_db_session” ----------
def require_db_session(fn):
    """
    Sustituto síncrono de Depends(get_session).
    Lo usas como @require_db_session encima de la vista.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with SessionLocal() as db:
            # pasa la sesión como keyword argument para que la vista la reciba
            kwargs["db"] = db
            return fn(*args, **kwargs)
    return wrapper























# routes/models_routes.py
from flask.views import MethodView
from flask_smorest import Blueprint

from src.core.manager_db_sync import require_db_session
from src.services.model_service import DemoDataService

blp = Blueprint(
    "models", "models",
    url_prefix="/models",
    description="Operaciones con modelos (sync)"
)

@blp.route("/demo-data")
class DemoDataList(MethodView):
    @blp.response(200)
    @require_db_session
    def get(self, db):
        """
        Listar todos los registros de demo_data
        (db es la sesión inyectada por el decorador)
        """
        data = DemoDataService(db).get_all_demo_data()
        return data











# core/auth_decorators.py
import os, time
from functools import wraps
from http import HTTPStatus
from flask import request, abort       # abort genera la respuesta 4xx

from src.core.manager_db_sync import require_db_session
from src.services.session_manager import SessionManager  # tu clase

def require_api_key_auth(fn):
    """
    ▸ Valida la cookie 'session_id'
    ▸ Borra sesiones expiradas
    ▸ (en DEV) crea una sesión dummy
    ▸ Inyecta `session_id` y `db` en la vista destino
    """
    @wraps(fn)
    @require_db_session              # <-- ¡recicla el decorador de BD!
    def wrapper(*args, db=None, **kwargs):

        session_manager = SessionManager(db)

        # Caso especial para entorno DEV
        if os.getenv("ELASTIC_APM_ENVIRONMENT") == "DEV":
            dummy_id = "3582edab-30c6-4a09-bbfa-e71c8abad410"
            session_manager.guardar_sesion(dummy_id, {
                "iden": "emalo@iberdrola.es",
                "groups": '["MB_M800127", "MB_M000051"]',
                "expires_at": time.time() + 3600 * 24 * 365
            })

        # Limpieza de sesiones caducadas
        session_manager.eliminar_sesiones_expiradas()

        # Cookie → session_id
        session_id = request.cookies.get("session_id")
        if not session_id:
            abort(HTTPStatus.FORBIDDEN, "No se encontró una sesión válida.")

        sesion = session_manager.obtener_sesion_valida(session_id)
        if not sesion:
            abort(HTTPStatus.FORBIDDEN,
                  "Sesión inválida o expirada. Logéate de nuevo.")

        # Pasamos la info a la vista
        kwargs["session_id"] = session_id
        return fn(*args, db=db, **kwargs)

    return wrapper



# routes/secure_routes.py
from flask.views import MethodView
from flask_smorest import Blueprint

from src.core.auth_decorators import require_api_key_auth


blp = Blueprint(
    "secure", "secure",
    url_prefix="/secure",
    description="Endpoints que requieren login"
)

@blp.route("/demo-data")
class DemoDataSecure(MethodView):

    @blp.response(200)
    @require_db_session      # ← 1º se inyecta `db`
    @require_api_key_auth    # ← 2º se valida la cookie usando `db`
    def get(self, db, session_id):
        """
        Ya dispones de:
        • db          → sesión de SQLAlchemy
        • session_id  → cookie validada
        """
        # … tu lógica …
        return {"ok": True, "session_id": session_id}

















# core/auth_decorators.py
import os
import time
from functools import wraps
from http import HTTPStatus

from flask import request, abort

from src.services.session_manager import SessionManager  # tu clase/service


def require_api_key_auth(fn):
    """
    ▸ Valida la cookie 'session_id' usando la BD.
    ▸ Espera que otro decorador (p. ej.  require_db_session) le inyecte 'db'.
    ▸ Si la sesión es válida, pasa 'session_id' a la vista.
    """
    @wraps(fn)
    def wrapper(*args, db=None, **kwargs):
        # --- Comprobamos que haya sesión de BD -----------------------------
        if db is None:
            raise RuntimeError(
                "require_api_key_auth necesita 'db' inyectado: "
                "asegúrate de usar primero @require_db_session"
            )

        sm = SessionManager(db)

        # --- Entorno DEV: crea una sesión dummy ----------------------------
        if os.getenv("ELASTIC_APM_ENVIRONMENT") == "DEV":
            dummy_id = "3582edab-30c6-4a09-bbfa-e71c8abad410"
            sm.guardar_sesion(dummy_id, {
                "iden": "emalo@iberdrola.es",
                "groups": '["MB_M800127", "MB_M000051"]',
                "expires_at": time.time() + 3600 * 24 * 365   # 1 año
            })

        # --- Limpia sesiones caducadas ------------------------------------
        sm.eliminar_sesiones_expiradas()

        # --- Obtén la cookie ----------------------------------------------
        session_id = request.cookies.get("session_id")
        if not session_id:
            abort(HTTPStatus.FORBIDDEN, "No se encontró una sesión válida.")

        # --- Verifica en BD ------------------------------------------------
        if not sm.obtener_sesion_valida(session_id):
            abort(
                HTTPStatus.FORBIDDEN,
                "Sesión inválida o expirada. Logéate de nuevo."
            )

        # --- Inyecta session_id y continúa --------------------------------
        kwargs["session_id"] = session_id
        return fn(*args, db=db, **kwargs)

    return wrapper