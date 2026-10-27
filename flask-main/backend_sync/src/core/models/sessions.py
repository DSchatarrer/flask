from datetime import datetime
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.models.base import Base


class Sessions(Base):
    __tablename__ = "sesiones"

    token: Mapped[str] = mapped_column(String(300), primary_key=True)
    usu: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"Sessions(usu={self.usu!r}, exp={self.exp!r})"
