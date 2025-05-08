# services/model_service.py

from sqlmodel import select
from sqlalchemy.orm import Session
from flask import abort

from http import HTTPStatus

try:
    from src.core.utils import to_json_compatible
    from src.models.models import DemoData, TiipoOxidacion, Location
except:
    from core.utils import to_json_compatible
    from models.models import DemoData, TiipoOxidacion, Location


class DemoDataService:
    def __init__(self, session):
        self.session = session

    def get_all_demo_data(self):
        statement = select(DemoData).order_by(DemoData.image_filename, DemoData.particion)
        data = self.session.execute(statement).scalars().all()

        if not data:
            abort(HTTPStatus.NOT_FOUND, description="No demo data found.")

        return to_json_compatible([d.dict() for d in data])
    
    def get_demo_data_by_filename_and_particion(self, image_filename: str, particion: int):
        statement = select(DemoData).where(
            DemoData.image_filename == image_filename,
            DemoData.particion == particion
        )
        result = self.session.execute(statement).scalar_one_or_none()

        if not result:
            abort(
                HTTPStatus.NOT_FOUND,
                description=f"No se encontraron datos para '{image_filename}' con partición {particion}."
            )

        return to_json_compatible(result.dict())
    

    def get_distinct_image_filenames(self):
        statement = (
            select(DemoData.image_filename)
            .distinct()
            .order_by(DemoData.image_filename)
        )
        result = self.session.execute(statement).scalars().all()

        if not result:
            abort(HTTPStatus.NOT_FOUND, description="No se encontraron image_filename distintos.")

        return to_json_compatible({"images": result})
        


