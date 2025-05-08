# src\services\blob_service.py


try:
    from src.core.utils import to_json_compatible
    from src.core.storage import BlobStorageManager
except:
    from core.utils import to_json_compatible
    from core.storage import BlobStorageManager



class BlobStorageService:
    def __init__(self, session):
        self.session = session
        self.blob_service = BlobStorageManager()

    def get_list_blobs(self, container_name: str):
        return self.blob_service.list_blobs(container_name)

    def get_list_containers(self):
        return self.blob_service.list_containers()

    def get_file_base64(self, container_name: str, blob_name: str, max_width: int = 500):
        return self.blob_service.get_blob_as_base64(container_name, blob_name, max_width)
    
    def get_related_images_base64(self, container_name: str, blob_name: str, max_width: int = 500):
        return self.blob_service.get_related_blobs_as_base64(container_name, blob_name, max_width)
    
    def get_json_dict(self, container_name: str, blob_name: str) -> dict:
        """
        Recupera un archivo JSON desde Azure Blob Storage como diccionario.
        
        Args:
            container_name (str): Nombre del contenedor.
            blob_name (str): Nombre del archivo (debe terminar en .json).

        Returns:
            dict: Diccionario con los datos o None si falla.
        """
        return self.blob_service.download_json_dict(container_name, blob_name)

