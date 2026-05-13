"""Task management endpoints with filtering and pagination."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.middleware.auth import role_required
from app.schemas.task import TaskCreateSchema, TaskUpdateSchema, TaskFilterSchema
from app.services import task_service

tasks_bp = Blueprint('tasks', __name__)
task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()
task_filter_schema = TaskFilterSchema()


@tasks_bp.route('', methods=['GET'])
@jwt_required()
def list_tasks():
    """List tasks with filtering, sorting, and pagination."""
    filters = task_filter_schema.load(request.args.to_dict())
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    current_role = claims.get('role', 'user')
    response, status_code = task_service.list_tasks(
        current_user_id=current_user_id,
        current_role=current_role,
        filters=filters,
    )
    return jsonify(response), status_code


@tasks_bp.route('', methods=['POST'])
@jwt_required()
@role_required('admin', 'project_manager')
def create_task():
    """Create a new task. Admin or PM only."""
    data = task_create_schema.load(request.get_json())
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    current_role = claims.get('role', 'user')
    response, status_code = task_service.create_task(
        data=data,
        current_user_id=current_user_id,
        current_role=current_role,
    )
    return jsonify(response), status_code


@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """Get a single task."""
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    current_role = claims.get('role', 'user')
    response, status_code = task_service.get_task(
        task_id=task_id,
        current_user_id=current_user_id,
        current_role=current_role,
    )
    return jsonify(response), status_code


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update a task. Users can only update status of their own tasks."""
    data = task_update_schema.load(request.get_json())
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    current_role = claims.get('role', 'user')
    response, status_code = task_service.update_task(
        task_id=task_id,
        data=data,
        current_user_id=current_user_id,
        current_role=current_role,
    )
    return jsonify(response), status_code


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin', 'project_manager')
def delete_task(task_id):
    """Delete a task. Admin or PM only."""
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    current_role = claims.get('role', 'user')
    response, status_code = task_service.delete_task(
        task_id=task_id,
        current_user_id=current_user_id,
        current_role=current_role,
    )
    return jsonify(response), status_code
