# src\routes\inference_routers.py

from flask.views import MethodView
from flask_smorest import Blueprint
from flask import Blueprint as FlaskBlueprint, jsonify 
from flask import request, current_app, render_template, redirect, url_for, session, flash
import cv2
import io
import base64
from matplotlib.figure import Figure
import numpy as np
import piexif
import os
import uuid
from datetime import datetime
import threading
import tensorflow as tf

try:
    from src.services.inference_service import InferenceService, get_class_masks_sahi
    from src.schemas.inference_schema import InferenceInputSchema
    from src.core.manager_db import require_db_session
    from src.core.storage import BlobStorageManager
except:
    from services.inference_service import InferenceService, get_class_masks_sahi
    from schemas.inference_schema import InferenceInputSchema
    from core.manager_db import require_db_session
    from core.storage import BlobStorageManager

def expandir_zonas_blancas(mask, n_iter=1, kernel_size=3):
    """
    Agranda todas las zonas blancas de una máscara binaria mediante dilatación.

    Args:
        mask: máscara binaria (uint8, 0 o 255).
        n_iter: número de iteraciones de dilatación (más = más expansión).
        kernel_size: tamaño del kernel estructurante.

    Returns:
        Máscara binaria (uint8) con zonas blancas agrandadas.
    """
    bin_mask = (mask > 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    dilatada = cv2.dilate(bin_mask, kernel, iterations=n_iter)
    return (dilatada * 255).astype(np.uint8)

blp = Blueprint("predict", "predict", url_prefix="/predict", description="Servicio de predicción")

@blp.route("/")
class PredictView(MethodView):
    @blp.arguments(InferenceInputSchema, location="form")
    @blp.response(200)
    def post(self, form_data):
        class_ids = form_data["class_ids"]
        image_file = request.files.get("image")  # archivo viene fuera del esquema

        if not image_file:
            return {"message": "Falta el archivo 'image'"}, 400

        try:
            class_ids_list = [int(x.strip()) for x in class_ids.split(",")]
        except Exception as e:
            return {"message": f"Error parseando class_ids: {str(e)}"}, 400

        service = InferenceService(current_app.config["curie_net"])
        result = service.run_inference(image_file.read(), class_ids_list)

        if "error" in result:
            return {"message": result["error"]}, 400

        return result
    
web_predict_bp = FlaskBlueprint("web_predict", __name__)

@web_predict_bp.route("/predict-web", methods=["GET", "POST"])
def predict_web():
    result = None
    img_data = {}

    if request.method == "POST":
        class_ids = request.form.get("class_ids")
        image_file = request.files.get("image")

        if not class_ids or not image_file:
            result = {"error": "Faltan datos"}
        else:
            try:
                # Leer imagen en memoria
                img_bytes = image_file.read()
                np_img = np.frombuffer(img_bytes, np.uint8)
                original_bgr = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
                if original_bgr is None:
                    raise ValueError("No se pudo decodificar la imagen")

                original = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)

                # Parsear class_ids y ejecutar inferencia
                class_ids_list = [int(x.strip()) for x in class_ids.split(",")]
                curie_net = current_app.config["curie_net"]

                masks = get_class_masks_sahi(
                    model=curie_net,
                    image_array=original_bgr,
                    class_ids=class_ids_list,
                    tile_size=(256, 256),
                    overlap_ratio=0.2,
                    batch_size=4,
                    threshold=0.5
                )

                oxido_mask = masks[class_ids_list[0]]
                if oxido_mask.shape != original.shape[:2]:
                    oxido_mask = cv2.resize(oxido_mask.astype(np.uint8), (original.shape[1], original.shape[0]))

                oxido_mask_dilatada = expandir_zonas_blancas(oxido_mask, n_iter=5, kernel_size=15)

                h, w = oxido_mask.shape
                if h > 2500 or w > 2500:
                    highlight_mask = oxido_mask.astype(bool)
                else:
                    highlight_mask = oxido_mask.astype(bool)
                overlay = original.copy()
                alpha = 0.5
                overlay[highlight_mask] = (
                    alpha * original[highlight_mask] + (1 - alpha) * np.array([255, 255, 0])
                ).astype(np.uint8)

                def to_base64(img, cmap=None):
                    fig = Figure(figsize=(4, 4))
                    ax = fig.subplots()
                    ax.imshow(img, cmap=cmap)
                    ax.axis("off")
                    buf = io.BytesIO()
                    fig.savefig(buf, format="png", bbox_inches="tight")
                    buf.seek(0)
                    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                    buf.close()
                    return img_base64

                img_data["original"] = to_base64(original)
                img_data["mask"] = to_base64(oxido_mask, cmap="gray")
                img_data["overlay"] = to_base64(overlay)

                result = {"message": "Predicción realizada con éxito"}

            except Exception as e:
                result = {"error": str(e)}

    return render_template("predict.html", result=result, img_data=img_data)

@web_predict_bp.route("/processing", methods=["POST"])
@require_db_session
def processing_web(db):
    class_ids = request.form.get("class_ids")
    image_files = request.files.getlist("image")

    if not class_ids or not image_files:
        return jsonify({"error": "Faltan datos: class_ids o imágenes"}), 400

    try:
        tiempo_estimado_min = len(image_files) * 3

        thread = threading.Thread(
            target=procesar_imagenes_en_segundo_plano,
            args=(image_files, current_app.config["curie_net"], current_app.config["pierre_net"] ),
            daemon=True
        )
        thread.start()

        return jsonify({
            "message": f"Procesamiento iniciado. Tiempo estimado: {tiempo_estimado_min} minutos.",
            "imagenes_recibidas": len(image_files),
            "estimado_minutos": tiempo_estimado_min
        }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def procesar_imagenes_en_segundo_plano(image_files, curie_net, pierre_net):
    try:
        from src.core.manager_db import get_session
    except:
        from core.manager_db import get_session

    session = get_session()

    for image_file in image_files:
        try:
            img_bytes = image_file.read()
            np_img = np.frombuffer(img_bytes, np.uint8)
            original_bgr = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if original_bgr is None:
                raise ValueError("No se pudo decodificar la imagen")

            original = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)

            masks = get_class_masks_sahi(
                model=curie_net,
                image_array=original_bgr,
                class_ids=[1],
                tile_size=(256, 256),
                overlap_ratio=0.2,
                batch_size=4,
                threshold=0.5
            )

            oxido_mask = masks[1]
            if oxido_mask.shape != original.shape[:2]:
                oxido_mask = cv2.resize(oxido_mask.astype(np.uint8), (original.shape[1], original.shape[0]))

            oxido_mask_dilatada = expandir_zonas_blancas(oxido_mask, n_iter=5, kernel_size=15)

            h, w = oxido_mask.shape
            highlight_mask = oxido_mask.astype(bool)

            overlay = original.copy()
            alpha = 0.5
            overlay[highlight_mask] = (
                alpha * original[highlight_mask] + (1 - alpha) * np.array([255, 255, 0])
            ).astype(np.uint8)

            # Aquí puedes guardar los resultados si es necesario
            print(f"✅ Imagen procesada correctamente: {image_file.filename}")

            masks2 = get_class_masks_from_array(
                "pierre_net",
                original,
                class_ids=[1,2],
                threshold=0.5
            )

            pipes_mask = masks2[1]
            estructure_mask = masks2[2]

            if pipes_mask.shape != original.shape[:2]:
                pipes_mask = cv2.resize(pipes_mask.astype(np.uint8), (original.shape[1], original.shape[0]))
            if estructure_mask.shape != original.shape[:2]:
                estructure_mask = cv2.resize(estructure_mask.astype(np.uint8), (original.shape[1], original.shape[0]))

            TYPE = "pipes"
            infra_mask = pipes_mask if TYPE == "pipes" else estructure_mask
            # Asegurar tamaños compatibles
            if infra_mask.shape != oxido_mask.shape:    
                oxido_mask = cv2.resize(oxido_mask.astype(np.uint8), (infra_mask.shape[1], infra_mask.shape[0]))
            
            # Convertir a uint8 por si acaso
            infra_mask_bin = (infra_mask > 0).astype(np.uint8)
            oxido_mask_bin = (oxido_mask > 0).astype(np.uint8)

            # Calcular intersección binaria
            interseccion_mask = cv2.bitwise_and(infra_mask_bin, oxido_mask_bin)
            interseccion_mask_vis = (interseccion_mask * 255).astype(np.uint8)
            highlight_mask = interseccion_mask_vis.astype(bool)
            overlay = original.copy()
            overlay[highlight_mask] = (
                alpha * original[highlight_mask] + (1 - alpha) * np.array([255, 255, 0])
            ).astype(np.uint8)

            get_coords = obtener_coordenadas_desde_bytes(img_bytes)
            proporcion = calcular_proporcion_interseccion(oxido_mask, infra_mask)

            base_name = os.path.splitext(image_file.filename)[0]

            imagen_original = base_name + ".png"
            imagen_procesada = base_name + "_processed.png"
            mask_interseccion_orginal_name = base_name + "_mask_intersect_original.png"
            mask_interseccion_plus_name = base_name + "_mask_intersect_plus.png"
            mask_oxido_name = base_name + "_mask_oxido.png"
            mask_tuberia_name = base_name + "_mask_pipe.png"
            mask_estructura_name = base_name + "_mask_struct.png"
            ubicacion = "dintel_13"
            container_img = "imagenes"
            container_mask = "mascaras"
            lat = get_coords[0]
            lon = get_coords[1]
            hoy = datetime.today().date()
            ahora = datetime.now().time()

            blob_manager = BlobStorageManager()
            blob_manager.upload_image_from_array("imagenes", imagen_original, original)
            blob_manager.upload_image_from_array("mascaras", imagen_procesada, overlay)
            blob_manager.upload_image_from_array("mascaras", mask_interseccion_orginal_name, interseccion_mask_vis)
            blob_manager.upload_image_from_array("mascaras", mask_interseccion_plus_name, oxido_mask_dilatada)
            blob_manager.upload_image_from_array("mascaras", mask_oxido_name, oxido_mask)
            blob_manager.upload_image_from_array("mascaras", mask_tuberia_name, pipes_mask)
            blob_manager.upload_image_from_array("mascaras", mask_estructura_name, estructure_mask)

            with session.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO demo_data (
                            image_filename, particion, ubicacion, latitud, longitud,
                            container_name_img, container_name_mask,
                            imagen_procesada_filename, mask_interseccion_orginal_filename,
                            mask_interseccion_plus_filename, mask_oxido_filename,
                            mask_tubos_filename, mask_estructura_filename,
                            dia, hora, porc_oxidacion_pipes
                        )
                        VALUES (
                            %s,
                            COALESCE(
                                (SELECT MAX(particion) + 1 FROM demo_data WHERE image_filename = %s),
                                0
                            ),
                            %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s
                        )
                    """, (
                        imagen_original,
                        imagen_original,
                        ubicacion,
                        lat,
                        lon,
                        container_img,
                        container_mask,
                        imagen_procesada,
                        mask_interseccion_orginal_name,
                        mask_interseccion_plus_name,
                        mask_oxido_name,
                        mask_tuberia_name,
                        mask_estructura_name,
                        hoy,
                        ahora,
                        round(proporcion, 2)
                    ))
            print("✅ Insert realizado correctamente")

            session.close()

            

        except Exception as e:
            print(f"❌ Error procesando imagen '{image_file.filename}': {e}")


def get_class_masks_from_array(model, original_bgr, class_ids, input_size=(256, 256), threshold=0.7):
    """
    Devuelve un diccionario de máscaras binarias para cada clase especificada.
    - original_bgr: imagen como ndarray (OpenCV, en BGR)
    - class_ids: lista de IDs de clases (ej: [1, 2])
    - Retorna: {id_clase: mascara_binaria (uint8, 0 y 255)}
    """
    if original_bgr is None:
        raise ValueError("Imagen inválida: NoneType")

    original_rgb = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(original_rgb, input_size)
    normalized = resized / 255.0

    pred_mask = model.predict(tf.convert_to_tensor([normalized]))[0]
    max_prob = np.max(pred_mask, axis=-1)
    pred_classes = np.argmax(pred_mask, axis=-1)
    pred_classes[max_prob < threshold] = 0

    original_size = (original_bgr.shape[1], original_bgr.shape[0])
    pred_mask_resized = cv2.resize(pred_classes, original_size, interpolation=cv2.INTER_NEAREST)

    class_masks = {}
    for class_id in class_ids:
        mask = np.where(pred_mask_resized == class_id, 255, 0).astype(np.uint8)
        class_masks[class_id] = mask

    return class_masks


def dms_a_decimal(dms, ref):
    grados, minutos, segundos = dms
    decimal = grados[0] / grados[1] + minutos[0] / minutos[1] / 60 + segundos[0] / segundos[1] / 3600
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def obtener_coordenadas_desde_bytes(image_bytes):
    try:
        exif_dict = piexif.load(image_bytes)
        gps = exif_dict.get("GPS", {})

        lat = gps[piexif.GPSIFD.GPSLatitude]
        lat_ref = gps[piexif.GPSIFD.GPSLatitudeRef].decode()

        lon = gps[piexif.GPSIFD.GPSLongitude]
        lon_ref = gps[piexif.GPSIFD.GPSLongitudeRef].decode()

        lat_decimal = dms_a_decimal(lat, lat_ref)
        lon_decimal = dms_a_decimal(lon, lon_ref)

        return (lat_decimal, lon_decimal)
    except KeyError:
        return {"coordenadas": None}
    except Exception as e:
        return {"error": str(e)}

def expandir_zonas_blancas(mask, n_iter=1, kernel_size=3):
    """
    Agranda todas las zonas blancas de una máscara binaria mediante dilatación.

    Args:
        mask: máscara binaria (uint8, 0 o 255).
        n_iter: número de iteraciones de dilatación (más = más expansión).
        kernel_size: tamaño del kernel estructurante.

    Returns:
        Máscara binaria (uint8) con zonas blancas agrandadas.
    """
    bin_mask = (mask > 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    dilatada = cv2.dilate(bin_mask, kernel, iterations=n_iter)
    return (dilatada * 255).astype(np.uint8)

def calcular_proporcion_interseccion(interseccion_ampliada: np.ndarray, pipes_mask: np.ndarray, factor_error: float = 0.00) -> float:
    """
    Calcula la proporción de píxeles en la intersección entre interseccion_ampliada y pipes_mask
    respecto al total de píxeles positivos en pipes_mask.

    Args:
        interseccion_ampliada (np.ndarray): Máscara booleana de intersección ampliada.
        pipes_mask (np.ndarray): Máscara booleana original de las tuberías.

    Returns:
        float: Proporción de píxeles de la intersección respecto a pipes_mask.
    """
    if interseccion_ampliada.shape != pipes_mask.shape:
        raise ValueError("Las máscaras deben tener el mismo tamaño")

    pixeles_interseccion = np.sum(interseccion_ampliada)
    pixeles_pipes = np.sum(pipes_mask)

    proporcion = (pixeles_interseccion / pixeles_pipes) -factor_error

    return proporcion if proporcion > 0 else 0.0

