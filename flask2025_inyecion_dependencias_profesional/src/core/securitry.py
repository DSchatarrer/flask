# src\core\securitry.py

from functools import wraps
from datetime import datetime, timedelta, timezone
from sqlmodel import Session
from sqlalchemy import delete
from flask import request, g
from flask_smorest import abort
from jose import jwt, JWTError
import uuid
from typing import Tuple


try:
    from src.core.settings import settings
    from src.models.sessions import Sessions
    from src.models.users import Users
except ImportError:
    from core.settings import settings
    from models.sessions import Sessions
    from models.users import Users


def create_token() -> str:
    """
    Genera un JWT firmado y con expiración.
    El 'sub' es un UUID aleatorio.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.TOKEN_SECONDS_EXP)

    data_token = {
        "sub": str(uuid.uuid4()),
        "exp": expires_at
        # (opcional) "iat": datetime.now(timezone.utc),
        # (opcional) "nbf": datetime.now(timezone.utc),
    }

    return jwt.encode(data_token, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> dict:
    """
    Verifica y decodifica un JWT. Lanza ValueError si es inválido o ha expirado.

    :param token: JWT a verificar
    :return: Payload del token si es válido
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Token inválido o expirado: {e}")
    
    
def get_uuid_and_exp_from_token(token: str) -> Tuple[str, datetime]:
    """
    Devuelve una tupla (uuid, exp) extraída del JWT.

    :param token: JWT a verificar
    :return: (uuid, exp) donde exp es un datetime timezone-aware en UTC
    """
    payload = verify_token(token)

    for field in ("sub", "exp"):
        if field not in payload:
            raise ValueError(f"El token no contiene el campo '{field}'")

    uuid_ = payload["sub"]
    exp_claim = payload["exp"]

    if isinstance(exp_claim, (int, float)):
        exp_dt = datetime.fromtimestamp(exp_claim, tz=timezone.utc)
    elif isinstance(exp_claim, datetime):
        exp_dt = exp_claim.astimezone(timezone.utc) if exp_claim.tzinfo else exp_claim.replace(tzinfo=timezone.utc)
    else:
        raise ValueError("Formato inesperado para el campo 'exp'")

    return uuid_, exp_dt

def purge_expired_sessions(db: Session) -> None:
    """Elimina todas las sesiones caducadas (exp < ahora UTC)."""
    stmt = (
        delete(Sessions)
        .where(Sessions.exp < datetime.now(timezone.utc))
    )
    db.exec(stmt)
    db.commit() 

def require_auth(*, roles: tuple[str, ...] | None = None):
    """
    Decorador de autorización.

    Parám:
        roles: tupla de roles aceptados. Si se deja en None, basta con que el
               token sea válido y la sesión esté viva.
    Uso:
        @blp.response(200)
        @require_db_session            # <<– 1º se inyecta la sesión
        @require_auth(roles=("admin", "user"))
        def get(self, *, db): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            db = kwargs.get("db")
            if db is None:
                abort(500, message="Falta la sesión de BD: pon primero @require_db_session")
                
            purge_expired_sessions(db)

            token_cookie = request.cookies.get("X-Sync.Ref")
            if not token_cookie:
                abort(401, message="No se encontró la cookie de autenticación")

            try:
                payload = verify_token(token_cookie)
            except ValueError as e:
                abort(401, message=str(e))

            uuid_ = payload.get("sub")
            if not uuid_:
                abort(401, message="Token sin identificador de sesión")

            sesion = (
                db.query(Sessions)
                  .filter(Sessions.token == uuid_)
                  .first()
            )
            if not sesion:
                abort(401, message="Sesión no encontrada")

            if sesion.exp < datetime.now(timezone.utc):
                abort(401, message="Sesión expirada")

            if roles is not None:
                user = (
                    db.query(Users)
                      .filter(Users.usu == sesion.usu)
                      .first()
                )
                if not user or user.role not in roles:
                    abort(403, message="Permisos insuficientes")

            # 5) Guardar info en flask.g para la vista que sigue
            # g.current_user = sesion.usu
            # g.token_payload = payload

            return view_func(*args, **kwargs)
        return wrapper
    return decorator


def require_secret_param(
    *,
    param_name: str = "secret",           # ?secret=XXXX
    header_name: str | None = None,       # p. ej. "X-Api-Key"
):
    """
    Exige que la petición incluya la clave secreta correcta.

    - Busca primero en query string (?secret=…).
    - Si `header_name` no es None, también permite enviarla en un header.
    - Compara con la variable de entorno `API_KEY`.

    Lanza 401 si:
      • falta el parámetro
      • o la clave es incorrecta
    """

    api_key_expected = settings.API_KEY
    if not api_key_expected:
        raise RuntimeError(
            f"La variable de entorno API_KEY no está definida — "
            "sin ella no puedo validar la API-Key."
        )

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            received_key = request.args.get(param_name)
            if header_name and not received_key:
                received_key = request.headers.get(header_name)

            if not received_key:
                abort(401, message=f"Falta API-Key ({param_name})")

            if received_key != api_key_expected:
                abort(401, message="No autorizado: clave secreta incorrecta")

            return view_func(*args, **kwargs)

        return wrapper
    return decorator


