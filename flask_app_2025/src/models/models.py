# src\models\models.py

from sqlmodel import SQLModel, Field, Column, PrimaryKeyConstraint, ForeignKey
import sqlalchemy.dialects.postgresql as pg
from typing import Optional
from sqlalchemy import CheckConstraint
from datetime import date, time


class DemoData(SQLModel, table=True):
    """
    Representa los datos de una imagen procesada, máscaras y metainformación.
    """
    __tablename__ = 'demo_data'
    __table_args__ = (
        PrimaryKeyConstraint("image_filename", "particion"),
    )

    image_filename: str = Field(sa_column=Column(pg.VARCHAR(255), nullable=False))
    particion: int = Field(sa_column=Column(pg.INTEGER, nullable=False))
    ubicacion: str = Field(sa_column=Column(pg.VARCHAR(250), nullable=True))
    latitud: float = Field(sa_column=Column(pg.FLOAT, nullable=True))
    longitud: float = Field(sa_column=Column(pg.FLOAT, nullable=True))
    container_name_img: str = Field(sa_column=Column(pg.VARCHAR(50), nullable=True))
    container_name_mask: str = Field(sa_column=Column(pg.VARCHAR(50), nullable=True))
    imagen_procesada_filename: str = Field(sa_column=Column(pg.VARCHAR(300), nullable=True))
    mask_interseccion_orginal_filename: str = Field(sa_column=Column(pg.VARCHAR(300), nullable=True))
    mask_interseccion_plus_filename: str = Field(sa_column=Column(pg.VARCHAR(300), nullable=True))
    mask_oxido_filename: str = Field(sa_column=Column(pg.VARCHAR(300), nullable=True))
    mask_tubos_filename: str = Field(sa_column=Column(pg.VARCHAR(300), nullable=True))
    mask_estructura_filename: str = Field(sa_column=Column(pg.VARCHAR(300), nullable=True))
    grado_oxidacion_id: Optional[int] = Field(default=None, sa_column=Column(pg.INTEGER, nullable=True))
    porc_oxidacion_pipes: Optional[float] = Field(default=None, sa_column=Column(pg.NUMERIC(5, 3), nullable=True))
    resolucion: Optional[str] = Field(default=None, sa_column=Column(pg.VARCHAR(100), nullable=True))
    filtros_img: Optional[str] = Field(default=None, sa_column=Column(pg.VARCHAR(500), nullable=True))
    dia: Optional[date] = Field(default=None, sa_column=Column(pg.DATE, nullable=True))
    hora: Optional[time] = Field(default=None, sa_column=Column(pg.TIME, nullable=True))
    notas_usu: Optional[str] = Field(default=None, sa_column=Column(pg.VARCHAR(1000), nullable=True))
    fav: Optional[bool] = Field(default=None, sa_column=Column(pg.BOOLEAN, nullable=True))

class TiipoOxidacion(SQLModel, table=True):
    """
    Representa un grado de oxidación con información química y color.
    """
    __tablename__ = 'oxidacion'

    grado_oxidacion_id: Optional[int] = Field(default=None, primary_key=True)
    elemento_periodico: str = Field(sa_column=Column(pg.VARCHAR(100), nullable=False))
    electron: str = Field(sa_column=Column(pg.VARCHAR(100), nullable=False))
    r: Optional[int] = Field(default=None, sa_column=Column(pg.INTEGER, nullable=True))
    g: Optional[int] = Field(default=None, sa_column=Column(pg.INTEGER, nullable=True))
    b: Optional[int] = Field(default=None, sa_column=Column(pg.INTEGER, nullable=True))
    h: Optional[int] = Field(default=None, sa_column=Column(pg.INTEGER, nullable=True))
    s: Optional[int] = Field(default=None, sa_column=Column(pg.INTEGER, nullable=True))
    v: Optional[int] = Field(default=None, sa_column=Column(pg.INTEGER, nullable=True))
    descripcion: Optional[str] = Field(default=None, sa_column=Column(pg.VARCHAR(500), nullable=True))
    oxidacion_localizada: Optional[float] = Field(default=None, sa_column=Column(pg.FLOAT, nullable=True))
    oxidacion_generalizada: Optional[float] = Field(default=None, sa_column=Column(pg.FLOAT, nullable=True))
    oxidacion_uniforme: Optional[float] = Field(default=None, sa_column=Column(pg.FLOAT, nullable=True))
    oxidacion_picadura: Optional[float] = Field(default=None, sa_column=Column(pg.FLOAT, nullable=True))
    oxidacion_exfoliacion: Optional[float] = Field(default=None, sa_column=Column(pg.FLOAT, nullable=True))


class Location(SQLModel, table=True):
    """
    Representa una zona geográfica delimitada, con su descripción y ubicación.
    """
    __tablename__ = 'location'

    zona_id: Optional[int] = Field(default=None, primary_key=True)
    poligono_delimitador: Optional[str] = Field(default=None, sa_column=Column(pg.TEXT, nullable=True))
    ubicacion: Optional[str] = Field(default=None, sa_column=Column(pg.VARCHAR(250), nullable=True))
    descripcion: Optional[str] = Field(default=None, sa_column=Column(pg.VARCHAR(500), nullable=True))
