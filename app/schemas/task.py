"""Task management schemas."""
from marshmallow import Schema, fields, validate


class TaskCreateSchema(Schema):
    """Schema for creating a task."""
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    description = fields.String(validate=validate.Length(max=5000))
    status = fields.String(validate=validate.OneOf(['todo', 'in_progress', 'review', 'done']))
    project_id = fields.Integer(required=True)
    assignee_id = fields.Integer(allow_none=True)
    due_date = fields.Date(allow_none=True)


class TaskUpdateSchema(Schema):
    """Schema for updating a task."""
    title = fields.String(validate=validate.Length(min=1, max=200))
    description = fields.String(validate=validate.Length(max=5000))
    status = fields.String(validate=validate.OneOf(['todo', 'in_progress', 'review', 'done']))
    assignee_id = fields.Integer(allow_none=True)
    due_date = fields.Date(allow_none=True)


class TaskFilterSchema(Schema):
    """Schema for task list query parameters."""
    status = fields.String(validate=validate.OneOf(['todo', 'in_progress', 'review', 'done']))
    assignee_id = fields.Integer()
    project_id = fields.Integer()
    sort_by = fields.String(validate=validate.OneOf(['created_at', 'updated_at', 'due_date', 'status']))
    sort_order = fields.String(validate=validate.OneOf(['asc', 'desc']))
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
