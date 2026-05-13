"""Authentication service — registration and login."""
import logging
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db
from app.models.user import User

logger = logging.getLogger(__name__)


def register_user(username: str, email: str, password: str, role: str = 'user'):
    """Register a new user account."""
    if User.query.filter_by(username=username).first():
        return {'error': {'code': 'CONFLICT', 'message': f'Username "{username}" is already taken.'}}, 409

    if User.query.filter_by(email=email).first():
        return {'error': {'code': 'CONFLICT', 'message': f'Email "{email}" is already registered.'}}, 409

    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    logger.info(f"User registered: {username} (role={role})")
    return {'message': 'User registered successfully.', 'user': user.to_dict()}, 201


def login_user(username: str, password: str):
    """Authenticate user and return JWT tokens."""
    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return {'error': {'code': 'UNAUTHORIZED', 'message': 'Invalid username or password.'}}, 401

    if not user.is_active:
        return {'error': {'code': 'FORBIDDEN', 'message': 'Account is deactivated. Contact an administrator.'}}, 403

    additional_claims = {'role': user.role, 'username': user.username}
    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)

    logger.info(f"User logged in: {username}")
    return {
        'message': 'Login successful.',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(),
    }, 200
