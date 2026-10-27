from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.models.base import Base


class Users(Base):
    __tablename__ = "usuarios"

    usu: Mapped[str] = mapped_column(String(255), primary_key=True)
    hash_pwd: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"Users(usu={self.usu!r}, role={self.role!r})"
