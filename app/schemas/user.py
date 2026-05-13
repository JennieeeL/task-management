"""User management schemas."""
from marshmallow import Schema, fields, validate


class UserUpdateSchema(Schema):
    """Schema for updating a user (admin operation)."""
    username = fields.String(validate=validate.Length(min=3, max=80))
    email = fields.Email(validate=validate.Length(max=120))
    password = fields.String(validate=validate.Length(min=8, max=128))
    role = fields.String(validate=validate.OneOf(['admin', 'project_manager', 'user']))
    is_active = fields.Boolean()
