"""Authentication endpoints: register, login, refresh, me."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
from app.schemas.auth import RegisterSchema, LoginSchema
from app.services import auth_service
from app.extensions import limiter

auth_bp = Blueprint('auth', __name__)
register_schema = RegisterSchema()
login_schema = LoginSchema()


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Register a new user account."""
    data = register_schema.load(request.get_json())
    response, status_code = auth_service.register_user(
        username=data['username'],
        email=data['email'],
        password=data['password'],
    )
    return jsonify(response), status_code


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Authenticate and receive JWT tokens."""
    data = login_schema.load(request.get_json())
    response, status_code = auth_service.login_user(
        username=data['username'],
        password=data['password'],
    )
    return jsonify(response), status_code


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh an access token using a valid refresh token."""
    identity = get_jwt_identity()
    claims = get_jwt()
    additional_claims = {'role': claims.get('role', ''), 'username': claims.get('username', '')}
    access_token = create_access_token(identity=identity, additional_claims=additional_claims)
    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Get the current authenticated user's profile."""
    from app.models.user import User
    from app.extensions import db
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': {'code': 'NOT_FOUND', 'message': 'User not found.'}}), 404
    return jsonify({'user': user.to_dict()}), 200
