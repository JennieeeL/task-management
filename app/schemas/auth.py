"""Authentication request schemas."""
from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    """Schema for user registration."""
    username = fields.String(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.String(required=True, validate=validate.Length(min=8, max=128))


class LoginSchema(Schema):
    """Schema for user login."""
    username = fields.String(required=True)
    password = fields.String(required=True)
