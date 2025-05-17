# src\schemas\login_schema.py

from marshmallow import Schema, fields

class LoginRequestSchema(Schema):
    user = fields.String(required=True, metadata={"example": "usuario1"})
    password = fields.String(required=True, metadata={"example": "mi_contraseña_segura"})
    role = fields.String(required=False, allow_none=True, metadata={"example": "role"})


class LoginResponseSchema(Schema):
    message = fields.String(required=True, metadata={"example": "Login correcto"})