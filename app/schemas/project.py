"""Project management schemas."""
from marshmallow import Schema, fields, validate


class ProjectCreateSchema(Schema):
    """Schema for creating a project."""
    name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    description = fields.String(validate=validate.Length(max=2000))
    status = fields.String(validate=validate.OneOf(['active', 'archived']))


class ProjectUpdateSchema(Schema):
    """Schema for updating a project."""
    name = fields.String(validate=validate.Length(min=1, max=120))
    description = fields.String(validate=validate.Length(max=2000))
    status = fields.String(validate=validate.OneOf(['active', 'archived']))


class ProjectMemberSchema(Schema):
    """Schema for adding a member to a project."""
    user_id = fields.Integer(required=True)
