# routes/models_routes.py

from flask.views import MethodView
from flask_smorest import Blueprint
import json
from flask import request
try:
    from src.services.model_service import DemoDataService
    from src.services.blob_service import BlobStorageService
    from src.core.manager_db import require_db_session
    from src.schemas.inference_schema import JsonWrapperSchema, RawJsonSchema
except:
    from services.model_service import DemoDataService
    from services.blob_service import BlobStorageService
    from core.manager_db import require_db_session
    from schemas.inference_schema import JsonWrapperSchema, RawJsonSchema
    
blp = Blueprint("models", "models", url_prefix="/models", description="Operaciones con modelos")


@blp.route("/demo-data")
class DemoDataList(MethodView):
    @blp.response(200)
    @require_db_session
    def get(self, db):
        """Listar todos los registros de demo_data"""
        data = DemoDataService(db).get_all_demo_data()
        return data
    
@blp.route("/demo-data/<string:image_filename>/<int:particion>")
class DemoDataByFilename(MethodView):
    @blp.response(200)
    @require_db_session
    def get(self, image_filename, particion, db):
        """Obtener un registro específico por image_filename y partición"""
        data = DemoDataService(db).get_demo_data_by_filename_and_particion(image_filename, particion)
        return data

@blp.route("/list-images")
class ImageList(MethodView):
    @blp.response(200)
    @require_db_session
    def get(self, db):
        """Listar todos los registros de demo_data"""
        data = DemoDataService(db).get_distinct_image_filenames()
        return data


@blp.route("/containers")
class ContainerList(MethodView):
    @blp.response(200)
    @require_db_session
    def get(self, db):
        """Listar todos los contenedores"""
        blob_service = BlobStorageService(db)
        containers = blob_service.get_list_containers()
        return {"containers": containers}


@blp.route("/blobs/<string:container_name>")
class BlobList(MethodView):
    @blp.response(200)
    @require_db_session
    def get(self, db, container_name):
        """Listar blobs dentro de un contenedor específico"""
        blob_service = BlobStorageService(db)
        blobs = blob_service.get_list_blobs(container_name)
        return {"container": container_name, "blobs": blobs}
    

@blp.route("/base64/<string:container_name>/<string:blob_name>")
@blp.route("/base64/<string:container_name>/<string:blob_name>/<int:max_width>")
class BlobAsBase64(MethodView):
    @blp.response(200)
    @require_db_session
    def get(self, db, container_name, blob_name, max_width=500):
        """
        Obtener un archivo como base64 desde Azure Blob Storage (con redimensionado opcional).
        Puedes usar /<max_width> como parte final del path (opcional).
        """
        result = BlobStorageService(db).get_file_base64(container_name, blob_name, max_width)

        if result is None:
            return {"error": "No se pudo obtener el archivo"}, 404

        return result
    

@blp.route("/base64-related/<string:container_name>/<string:blob_name>")
@blp.route("/base64-related/<string:container_name>/<string:blob_name>/<int:max_width>")
class RelatedBlobsAsBase64(MethodView):
    @blp.response(200)
    @require_db_session
    def get(self, db, container_name, blob_name, max_width=500):
        """
        Obtener todas las imágenes relacionadas con un archivo (por nombre base) como base64 desde Azure Blob Storage.
        Puedes especificar opcionalmente el ancho máximo como último segmento de la URL.
        """
        result = BlobStorageService(db).get_related_images_base64(container_name, blob_name, max_width)

        if not result:
            return {"error": f"No se encontraron imágenes relacionadas con '{blob_name}' en '{container_name}'"}, 404

        return result

@blp.route("/json/<string:container_name>/<string:blob_name>")
class JsonFromBlob(MethodView):
    @blp.response(200)
    @require_db_session
    def get(self, db, container_name, blob_name):
        """
        Obtener un archivo .json desde Azure Blob Storage como diccionario.
        """
        blob_service = BlobStorageService(db)
        result = blob_service.get_json_dict(container_name, blob_name)
        diccionario = json.loads(result)

        if diccionario is None:
            return {"error": f"No se pudo recuperar el JSON '{blob_name}' desde el contenedor '{container_name}'"}, 404

        return diccionario

    




