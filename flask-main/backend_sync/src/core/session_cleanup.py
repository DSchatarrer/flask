"""Mantenimiento de sesiones; nunca ejecutarlo desde un guard HTTP."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session
from src.core.models.sessions import Sessions


def cleanup_expired_sessions(db: Session, *, retention_days: int = 7, now: datetime | None = None) -> int:
    """Elimina sesiones caducadas tras retención; el llamador gestiona commit."""
    if retention_days < 0:
        raise ValueError("retention_days debe ser >= 0")
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        raise ValueError("now debe incluir zona horaria")
    cutoff = reference.astimezone(timezone.utc) - timedelta(days=retention_days)
    result = db.execute(delete(Sessions).where(Sessions.exp.is_not(None), Sessions.exp <= cutoff))
    return result.rowcount or 0
