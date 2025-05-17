# src\models\sessions.py


from sqlalchemy import func
from sqlmodel import SQLModel, Field, Relationship, Column, ForeignKey
from datetime import datetime
import sqlalchemy.dialects.postgresql as pg


class Sessions(SQLModel, table=True):
    """
    Modelo para la tabla email.
    """
    __tablename__ = 'sesiones'

    token: str = Field(sa_column=Column(pg.VARCHAR(300), primary_key=True, nullable=False))
    usu: str = Field(sa_column=Column(pg.VARCHAR(255), nullable=True))
    exp: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=True))
    
    def _repr_(self) -> str:
        return f"Sessions(usu='{self.usu}', exp='{self.exp}')"