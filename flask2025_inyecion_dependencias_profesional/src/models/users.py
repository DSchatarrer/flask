# src\applications\etl\models.py

from sqlalchemy import func
from sqlmodel import SQLModel, Field, Relationship, Column, ForeignKey
from datetime import datetime
import sqlalchemy.dialects.postgresql as pg


class Users(SQLModel, table=True):
    """
    Modelo para la tabla email.
    """
    __tablename__ = 'usuarios'

    usu: str = Field(sa_column=Column(pg.VARCHAR(255), primary_key=True, nullable=False))
    hash_pwd: str = Field(sa_column=Column(pg.VARCHAR(255), nullable=True))
    role: str = Field(sa_column=Column(pg.VARCHAR(255), nullable=True))
    
    def _repr_(self) -> str:
        return f"Users(usu='{self.user}', role='{self.role}')"