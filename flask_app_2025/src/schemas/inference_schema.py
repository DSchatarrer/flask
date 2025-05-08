# src/schemas/inference_schema.py

from marshmallow import Schema, fields

class InferenceInputSchema(Schema):
    class_ids = fields.Str(required=True, metadata={"description": "IDs de clase separados por coma"})

class JsonWrapperSchema(Schema):
    data = fields.Dict(keys=fields.Str(), values=fields.Raw())

class RawJsonSchema(Schema):
    __schema_type__ = "object"
    __schema_example__ = {
        "oxidacion_localizada": 0.0,
        "oxidacion_generalizada": 1.22,
        "mask_name": "nombre_mask.png",
        "centroid_colors": [[49.0, 51.4, 40.9], [125.4, 86.9, 51.6]]
    }