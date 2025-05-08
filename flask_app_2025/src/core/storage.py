
from azure.storage.blob import BlobServiceClient
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import re
import json
from typing import Dict

ADM_SECRET = 'xxx'
ACCOUNT_NAME = "xxx"

class BlobStorageManager:
    # def __init__(self, tenant_id, client_id, client_secret, account_name):
    #     self.account_url = f"https://{account_name}.blob.core.windows.net"
    #     self.credential = ClientSecretCredential(
    #         tenant_id=tenant_id,
    #         client_id=client_id,
    #         client_secret=client_secret
    #     )
    #     self.blob_service_client = BlobServiceClient(
    #         account_url=self.account_url,
    #         credential=self.credential
    #     )

    def __init__(self, account_name:str=ACCOUNT_NAME, account_key:str=ADM_SECRET):
        self.account_url = f"https://{account_name}.blob.core.windows.net"
        self.blob_service_client = BlobServiceClient(
            account_url=self.account_url,
            credential=account_key
        )

    def ensure_container(self, container_name):
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container()
                print(f"📁 Contenedor '{container_name}' creado.")
            else:
                print(f"📁 Contenedor '{container_name}' ya existe.")
        except Exception as e:
            print("❌ Error al asegurar el contenedor:", e)

    def upload_file(self, container_name, blob_name, file_path):
        try:
            self.ensure_container(container_name)
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            print(f"📤 Archivo '{file_path}' subido como '{blob_name}' en '{container_name}'.")
        except Exception as e:
            print("❌ Error al subir archivo:", e)

    def upload_file_from_memory(self, container_name, blob_name, file_bytes):
        try:
            self.ensure_container(container_name)
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)

            # Puedes pasar directamente file_bytes (tipo bytes o BytesIO)
            blob_client.upload_blob(file_bytes, overwrite=True)

            print(f"📤 Archivo '{blob_name}' subido correctamente en '{container_name}'.")
        except Exception as e:
            print("❌ Error al subir archivo desde memoria:", e)

    def upload_file_from_base64(self, container_name, blob_name, base64_data):
        """
        Sube un archivo a Azure Blob Storage desde una cadena base64 sin escribir en disco.
        """
        try:
            self.ensure_container(container_name)
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)

            # Convertir base64 a bytes
            file_bytes = base64.b64decode(base64_data)

            # Subir desde memoria
            blob_client.upload_blob(BytesIO(file_bytes), overwrite=True)

            print(f"📤 Archivo '{blob_name}' subido a contenedor '{container_name}' desde base64.")
        except Exception as e:
            print("❌ Error al subir archivo desde base64:", e)

    def download_file(self, container_name, blob_name, download_path):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            with open(download_path, "wb") as file:
                stream = blob_client.download_blob()
                file.write(stream.readall())
            print(f"📥 Archivo '{blob_name}' descargado a '{download_path}'.")
        except Exception as e:
            print("❌ Error al descargar archivo:", e)

    def delete_blob(self, container_name, blob_name):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            blob_client.delete_blob()
            print(f"🗑️ Archivo '{blob_name}' eliminado de '{container_name}'.")
        except Exception as e:
            print("❌ Error al eliminar archivo:", e)

    def list_blobs(self, container_name: str):
        """
        Lista los blobs dentro de un contenedor.

        Retorna:
            List[Dict[str, Any]]: Lista de blobs con nombre y tamaño.
        """
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blobs = container_client.list_blobs()
            blob_list = [
                {"name": blob.name, "size": blob.size, "content_type": getattr(blob, "content_settings", {}).get("content_type", None)}
                for blob in blobs
            ]

            print(f"📂 Archivos en '{container_name}':")
            for blob in blob_list:
                print(f" - {blob['name']} ({blob['size']} bytes)")

            return blob_list
        except Exception as e:
            print("❌ Error al listar blobs:", e)
            return []

    def get_blob_as_base64(self, container_name: str, blob_name: str, max_width: int = 500):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            blob_data = blob_client.download_blob().readall()

            image = Image.open(BytesIO(blob_data))

            w_percent = max_width / float(image.size[0])
            new_height = int((float(image.size[1]) * float(w_percent)))
            image = image.resize((max_width, new_height), Image.LANCZOS)

            output_buffer = BytesIO()
            image_format = image.format if image.format else 'PNG'
            image.save(output_buffer, format=image_format)
            resized_bytes = output_buffer.getvalue()

            base64_data = base64.b64encode(resized_bytes).decode("utf-8")

            return {
                "file_name": blob_name,
                "data": base64_data
            }
        except Exception as e:
            print("❌ Error al obtener el archivo en base64:", e)
            return None

    def list_containers(self) -> Dict:
        """
        Lista todos los contenedores en la cuenta de almacenamiento.
        """
        try:
            containers = self.blob_service_client.list_containers()
            print("📦 Contenedores existentes:")
            return [container.name for container in containers]
        except Exception as e:
            print("❌ Error al listar contenedores:", e)
            return []

    def create_container(self, container_name):
        """
        Crea un contenedor si no existe.
        """
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container()
                print(f"📁 Contenedor '{container_name}' creado.")
            else:
                print(f"ℹ️ Contenedor '{container_name}' ya existe.")
        except Exception as e:
            print("❌ Error al crear contenedor:", e)

    def delete_container(self, container_name):
        """
        Elimina un contenedor de Azure Blob Storage.
        """
        try:
            self.blob_service_client.delete_container(container_name)
            print(f"🗑️ Contenedor '{container_name}' eliminado.")
        except Exception as e:
            print("❌ Error al eliminar contenedor:", e)

    def upload_image_from_array(self, container_name, blob_name, array):
        """
        Sube una imagen (RGB o máscara en escala de grises) desde un array numpy (sin escribir en disco).
        - array (n,m) → máscara en escala de grises (L)
        - array (n,m,3) → imagen RGB
        """
        try:
            self.ensure_container(container_name)

            # Detectar modo de imagen
            if array.ndim == 2:
                mode = 'L'  # grayscale
            elif array.ndim == 3 and array.shape[2] == 3:
                mode = 'RGB'
            else:
                raise ValueError("Solo se permiten arrays (n,m) para máscaras o (n,m,3) para imágenes RGB.")

            # Convertir a imagen
            image = Image.fromarray(np.uint8(array), mode=mode)

            # Guardar en memoria
            img_bytes = BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            # Subir a Azure Blob
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            blob_client.upload_blob(img_bytes, overwrite=True)

            print(f"🖼️ Imagen '{blob_name}' subida a contenedor '{container_name}'.")

        except Exception as e:
            print("❌ Error al subir la imagen desde array:", e)

    def list_blobs(self, container_name):
        """
        Lista los blobs dentro de un contenedor.

        Retorna:
            List[str]: Lista de nombres de archivos (blobs).
        """
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blobs = container_client.list_blobs()
            blob_names = [blob.name for blob in blobs]

            print(f"📂 Archivos en '{container_name}':")
            for name in blob_names:
                print(f" - {name}")

            return blob_names
        except Exception as e:
            print("❌ Error al listar blobs:", e)
            return []
        
    def upload_image_from_array(self, container_name, blob_name, array):
        try:
            self.ensure_container(container_name)

            # Detectar modo de imagen
            if array.ndim == 2:
                mode = 'L'  # escala de grises
            elif array.ndim == 3 and array.shape[2] == 3:
                mode = 'RGB'
            else:
                raise ValueError("Solo se permiten arrays (n,m) para máscaras o (n,m,3) para imágenes RGB.")

            # Convertir a imagen
            image = Image.fromarray(np.uint8(array), mode=mode)

            # Guardar en memoria y subir
            img_bytes = BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            blob_client.upload_blob(img_bytes, overwrite=True)

            print(f"🖼️ Imagen '{blob_name}' subida a contenedor '{container_name}'.")

        except Exception as e:
            print("❌ Error al subir la imagen desde array:", e)


    def get_related_blobs_as_base64(self, container_name: str, blob_name: str, max_width: int = 500):
        try:
            result = []

            def resize_and_encode_image(container: str, blob: str):
                blob_client = self.blob_service_client.get_blob_client(container=container, blob=blob)
                blob_data = blob_client.download_blob().readall()

                image = Image.open(BytesIO(blob_data))

                w_percent = max_width / float(image.size[0])
                new_height = int((float(image.size[1]) * float(w_percent)))
                image = image.resize((max_width, new_height), Image.LANCZOS)

                output_buffer = BytesIO()
                image_format = image.format if image.format else 'PNG'
                image.save(output_buffer, format=image_format)
                resized_bytes = output_buffer.getvalue()

                base64_data = base64.b64encode(resized_bytes).decode("utf-8")

                return {
                    "file_name": blob,
                    "container": container,
                    "data": base64_data
                }

            # Parte 1: blobs relacionados en el contenedor dado (filtrando por imágenes)
            base_name = re.sub(r'\.[^.]+$', '', blob_name)
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_list = container_client.list_blobs()

            image_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
            matching_blobs = [
                b.name for b in blob_list
                if base_name in b.name and b.name.lower().endswith(image_exts)
            ]

            for name in matching_blobs:
                try:
                    result.append(resize_and_encode_image(container_name, name))
                except Exception as e:
                    print(f"⚠️ Error al procesar {name} en {container_name}:", e)

            # Parte 2: añadir la imagen original desde el contenedor fijo "imagenes"
            try:
                result.append(resize_and_encode_image("imagenes", blob_name))
            except Exception as e:
                print(f"⚠️ Imagen original '{blob_name}' no encontrada en contenedor 'imagenes':", e)

            return {"data": result}

        except Exception as e:
            print("❌ Error general al obtener imágenes relacionadas:", e)
            return []
        
    def upload_json_dict(self, container_name, blob_name, json_dict):
        """
        Sube un diccionario como archivo JSON a Azure Blob Storage.
        
        Args:
            container_name (str): Nombre del contenedor.
            blob_name (str): Nombre del archivo blob (debe terminar en .json).
            json_dict (dict): Diccionario a guardar.
        """
        try:
            self.ensure_container(container_name)

            json_data = json.dumps(json_dict, indent=4)
            json_bytes = BytesIO(json_data.encode("utf-8"))

            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            blob_client.upload_blob(json_bytes, overwrite=True)

            print(f"📄 JSON '{blob_name}' subido a contenedor '{container_name}'.")
        except Exception as e:
            print("❌ Error al subir JSON:", e)

    def download_json_dict(self, container_name, blob_name):
        """
        Descarga un archivo JSON desde Azure Blob Storage y lo convierte en un diccionario.

        Args:
            container_name (str): Nombre del contenedor.
            blob_name (str): Nombre del archivo JSON (debe terminar en .json).

        Returns:
            dict: Diccionario con el contenido del JSON o None si falla.
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            blob_data = blob_client.download_blob().readall()
            json_dict = json.loads(blob_data.decode("utf-8"))
            print(f"📥 JSON '{blob_name}' recuperado desde '{container_name}'.")
            return json_dict
        except Exception as e:
            print("❌ Error al descargar el JSON:", e)
            return None
