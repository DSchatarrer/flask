from marshmallow import Schema, fields


class GreetingSchema(Schema):
    hola = fields.String(required=True)
