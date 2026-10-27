from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Metadata compartida; no almacena engine ni sesiones."""
