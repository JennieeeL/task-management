"""User management endpoints (admin only)."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.middleware.auth import role_required
from app.schemas.user import UserUpdateSchema
from app.services import user_service

users_bp = Blueprint('users', __name__)
user_update_schema = UserUpdateSchema()


@users_bp.route('', methods=['GET'])
@jwt_required()
@role_required('admin')
def list_users():
    """List all users with pagination. Admin only."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    response, status_code = user_service.list_users(page=page, per_page=per_page)
    return jsonify(response), status_code


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_user(user_id):
    """Get a user by ID. Admin only."""
    response, status_code = user_service.get_user(user_id)
    return jsonify(response), status_code


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_user(user_id):
    """Update a user. Admin only."""
    data = user_update_schema.load(request.get_json())
    response, status_code = user_service.update_user(user_id, data)
    return jsonify(response), status_code


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_user(user_id):
    """Soft-delete (deactivate) a user. Admin only."""
    response, status_code = user_service.delete_user(user_id)
    return jsonify(response), status_code
