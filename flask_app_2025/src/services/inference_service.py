# src\services\inference_service.py

import numpy as np
import tensorflow as tf
import base64
import cv2
from typing import List, Dict, Tuple

def get_class_masks_sahi(
    model: tf.keras.Model,
    image_array: np.ndarray,
    class_ids: List[int] = [1],
    tile_size: Tuple[int, int] = (256, 256),
    overlap_ratio: float = 0.2,
    batch_size: int = 8,
    threshold: float = 0.7
) -> Dict[int, np.ndarray]:
    """
    Implementación mejorada con SAHI y procesamiento por lotes
    
    Args:
        model: Modelo de segmentación con input (256,256,3) y output (256,256,num_classes)
        image_path: Ruta de la imagen a procesar
        class_ids: Lista de IDs de clases a segmentar
        tile_size: Tamaño de entrada requerido por el modelo (256,256)
        overlap_ratio: Solapamiento entre tiles (0.0-0.5)
        batch_size: Número de tiles a procesar en paralelo
        threshold: Umbral de probabilidad para predicciones
    
    Returns:
        Diccionario con máscaras binarias para cada clase (0-255)
    """
    img = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    tile_h, tile_w = tile_size
    
    stride_h = int(tile_h * (1 - overlap_ratio))
    stride_w = int(tile_w * (1 - overlap_ratio))
    
    y_coords = []
    x_coords = []
    tiles = []
    
    for y in range(0, h, stride_h):
        for x in range(0, w, stride_w):
            y1 = max(0, y)
            y2 = min(h, y + tile_h)
            x1 = max(0, x)
            x2 = min(w, x + tile_w)
            
            tile = img[y1:y2, x1:x2]
            pad_y = tile_h - (y2 - y1)
            pad_x = tile_w - (x2 - x1)
            
            if pad_y > 0 or pad_x > 0:
                tile = np.pad(tile, 
                            ((0, pad_y), (0, pad_x), (0, 0)),
                            mode='constant')
            
            tiles.append(tile)
            y_coords.append((y1, y2))
            x_coords.append((x1, x2))
    
    dataset = tf.data.Dataset.from_tensor_slices(tiles)
    dataset = dataset.map(lambda x: tf.cast(x, tf.float32)/255.0,
                        num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    
    window = np.outer(np.hanning(tile_h), np.hanning(tile_w))
    window = np.expand_dims(window, axis=-1)  # (256,256,1)
    
    num_classes = model.output_shape[-1]
    prob_maps = np.zeros((h, w, num_classes), dtype=np.float32)
    weight_maps = np.zeros((h, w), dtype=np.float32)
    
    for batch_idx, batch_tiles in enumerate(dataset):
        preds = model.predict(batch_tiles, verbose=0)
        
        for i in range(preds.shape[0]):
            tile_idx = batch_idx * batch_size + i
            if tile_idx >= len(tiles):
                break
                
            y1, y2 = y_coords[tile_idx]
            x1, x2 = x_coords[tile_idx]
            actual_h = y2 - y1
            actual_w = x2 - x1
            
            weighted_pred = preds[i][:actual_h, :actual_w] * window[:actual_h, :actual_w]
            
            prob_maps[y1:y2, x1:x2] += weighted_pred
            weight_maps[y1:y2, x1:x2] += window[:actual_h, :actual_w, 0]
    
    prob_maps /= np.maximum(weight_maps[..., np.newaxis], 1e-7)
    
    max_probs = np.max(prob_maps, axis=-1)
    pred_classes = np.argmax(prob_maps, axis=-1)
    
    class_masks = {}
    for cid in class_ids:
        mask = np.zeros((h, w), dtype=np.uint8)
        class_mask = (pred_classes == cid) & (max_probs >= threshold)
        mask[class_mask] = 255
        class_masks[cid] = mask
    
    return class_masks

class InferenceService:
    def __init__(self, model: tf.keras.Model):
        self.model = model

    def run_inference(self, image_bytes: bytes, class_ids: List[int]) -> Dict[str, str]:
        try:
            file_bytes = np.frombuffer(image_bytes, np.uint8)
            image_array = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            if image_array is None:
                return {"error": "No se pudo decodificar la imagen"}

            masks = get_class_masks_sahi(
                model=self.model,
                image_array=image_array,
                class_ids=class_ids
            )

            encoded_masks = {}
            for cid, mask in masks.items():
                _, buffer = cv2.imencode(".png", mask)
                encoded = base64.b64encode(buffer).decode("utf-8")
                encoded_masks[str(cid)] = encoded

            return {"masks": encoded_masks}

        except Exception as e:
            return {"error": f"Error en la inferencia: {str(e)}"}
