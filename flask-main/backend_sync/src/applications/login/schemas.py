from marshmallow import Schema, fields, validate


class LoginRequestSchema(Schema):
    user = fields.String(required=True, validate=validate.Length(min=1))
    password = fields.String(required=True, validate=validate.Length(min=1))


class RegisterRequestSchema(LoginRequestSchema):
    role = fields.String(required=True, validate=validate.Length(min=1))


class MessageSchema(Schema):
    message = fields.String(required=True)
