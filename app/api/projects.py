"""Project management endpoints."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.middleware.auth import role_required
from app.schemas.project import ProjectCreateSchema, ProjectUpdateSchema, ProjectMemberSchema
from app.services import project_service

projects_bp = Blueprint('projects', __name__)
project_create_schema = ProjectCreateSchema()
project_update_schema = ProjectUpdateSchema()
member_schema = ProjectMemberSchema()


@projects_bp.route('', methods=['GET'])
@jwt_required()
def list_projects():
    """List projects (filtered by role)."""
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    current_role = claims.get('role', 'user')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    response, status_code = project_service.list_projects(
        current_user_id=current_user_id,
        current_role=current_role,
        page=page,
        per_page=per_page,
    )
    return jsonify(response), status_code


@projects_bp.route('', methods=['POST'])
@jwt_required()
@role_required('admin', 'project_manager')
def create_project():
    """Create a new project. Admin or PM only."""
    data = project_create_schema.load(request.get_json())
    current_user_id = int(get_jwt_identity())
    response, status_code = project_service.create_project(
        name=data['name'],
        description=data.get('description'),
        owner_id=current_user_id,
        status=data.get('status', 'active'),
    )
    return jsonify(response), status_code


@projects_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """Get project details with members."""
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    current_role = claims.get('role', 'user')
    response, status_code = project_service.get_project(
        project_id=project_id,
        current_user_id=current_user_id,
        current_role=current_role,
    )
    return jsonify(response), status_code


@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
@role_required('admin', 'project_manager')
def update_project(project_id):
    """Update a project. Admin or PM (own projects) only."""
    data = project_update_schema.load(request.get_json())
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    current_role = claims.get('role', 'user')
    response, status_code = project_service.update_project(
        project_id=project_id,
        data=data,
        current_user_id=current_user_id,
        current_role=current_role,
    )
    return jsonify(response), status_code


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin', 'project_manager')
def delete_project(project_id):
    """Delete a project. Admin only/project manager (own projects) only."""
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    current_role = claims.get('role', 'user')
    response, status_code = project_service.delete_project(
        project_id=project_id,
        current_user_id=current_user_id,
        current_role=current_role,
    )
    return jsonify(response), status_code


@projects_bp.route('/<int:project_id>/members', methods=['POST'])
@jwt_required()
@role_required('admin', 'project_manager')
def add_member(project_id):
    """Add a member to a project."""
    data = member_schema.load(request.get_json())
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    current_role = claims.get('role', 'user')
    response, status_code = project_service.add_member(
        project_id=project_id,
        user_id=data['user_id'],
        current_user_id=current_user_id,
        current_role=current_role,
    )
    return jsonify(response), status_code


@projects_bp.route('/<int:project_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin', 'project_manager')
def remove_member(project_id, user_id):
    """Remove a member from a project."""
    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    current_role = claims.get('role', 'user')
    response, status_code = project_service.remove_member(
        project_id=project_id,
        user_id=user_id,
        current_user_id=current_user_id,
        current_role=current_role,
    )
    return jsonify(response), status_code
