"""Autenticación/roles read-only: no ejecutar DELETE, COMMIT ni limpieza aquí."""
from datetime import datetime, timedelta, timezone
from functools import wraps
from hmac import compare_digest
from typing import Any
from uuid import uuid4

from flask import current_app, g, request
from flask_smorest import abort
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.core.models.sessions import Sessions
from src.core.models.users import Users


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_utc(value: datetime) -> datetime:
    """Los drivers como SQLite pueden entregar fechas naive: se guardan en UTC."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def create_token() -> str:
    payload = {
        "sub": str(uuid4()),
        "iat": utc_now(),
        "exp": utc_now() + timedelta(seconds=current_app.config["TOKEN_SECONDS_EXP"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm=current_app.config["JWT_ALGORITHM"])


def verify_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token, current_app.config["JWT_SECRET_KEY"],
            algorithms=[current_app.config["JWT_ALGORITHM"]],
            options={"require_exp": True, "require_sub": True},
        )
    except JWTError as exc:
        raise ValueError("Token inválido o expirado") from exc


def get_uuid_and_exp_from_token(token: str) -> tuple[str, datetime]:
    payload = verify_token(token)
    return str(payload["sub"]), datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)


def require_auth(*, roles: tuple[str, ...] | None = None):
    """Valida JWT + sesión persistida + usuario; opcionalmente rol (compatibilidad)."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            db: Session | None = kwargs.get("db")
            if db is None:
                raise RuntimeError("@require_db_session debe ser el decorador externo a @require_auth")
            token = request.cookies.get("X-Sync.Ref")
            if not token:
                abort(401, message="Falta la cookie de autenticación")
            try:
                payload = verify_token(token)
            except ValueError:
                abort(401, message="Token inválido o expirado")
            session_id = str(payload.get("sub", ""))
            active_session = db.get(Sessions, session_id) if session_id else None
            if not active_session or active_session.exp is None or normalize_utc(active_session.exp) <= utc_now():
                abort(401, message="Sesión inexistente o expirada")
            user = db.get(Users, active_session.usu) if active_session.usu else None
            if user is None:
                abort(401, message="Usuario inexistente")
            g.current_user = user
            g.auth_session_id = session_id
            if roles is not None and user.role not in roles:
                abort(403, message="Permisos insuficientes")
            return view_func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*allowed_roles: str):
    """Solo autoriza; usar después de require_auth. No altera ninguna tabla."""
    if not allowed_roles:
        raise ValueError("Indica al menos un rol")
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if user is None:
                abort(401, message="Autenticación requerida")
            if user.role not in allowed_roles:
                abort(403, message="Permisos insuficientes")
            return view_func(*args, **kwargs)
        return wrapper
    return decorator


def require_secret_param(*, param_name: str = "apikey", header_name: str | None = "X-API-Key"):
    """Admite header seguro preferente y ?apikey= legado (deprecated)."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            provided = request.headers.get(header_name) if header_name else None
            if not provided:
                provided = request.args.get(param_name)
            expected = current_app.config["API_KEY"]
            if not provided or not compare_digest(provided.encode("utf-8"), expected.encode("utf-8")):
                abort(401, message="API key ausente o incorrecta")
            return view_func(*args, **kwargs)
        return wrapper
    return decorator
