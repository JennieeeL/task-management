"""User management service (admin operations)."""
import logging
from app.extensions import db
from app.models.user import User
from app.utils.pagination import paginate_query

logger = logging.getLogger(__name__)


def list_users(page: int = 1, per_page: int = 20) -> tuple[dict, int]:
    """List all users with pagination."""
    query = User.query.order_by(User.created_at.desc())
    result = paginate_query(query, page=page, per_page=per_page)
    return {
        'users': [u.to_dict() for u in result['items']],
        'pagination': result['pagination'],
    }, 200


def get_user(user_id: int) -> tuple[dict, int]:
    """Get a single user by ID."""
    user = db.session.get(User, user_id)
    if not user:
        return {'error': {'code': 'NOT_FOUND', 'message': f'User with id {user_id} not found.'}}, 404
    return {'user': user.to_dict()}, 200


def update_user(user_id: int, data: dict) -> tuple[dict, int]:
    """Update user details (admin operation)."""
    user = db.session.get(User, user_id)
    if not user:
        return {'error': {'code': 'NOT_FOUND', 'message': f'User with id {user_id} not found.'}}, 404

    if 'username' in data:
        existing = User.query.filter(User.username == data['username'], User.id != user_id).first()
        if existing:
            return {'error': {'code': 'CONFLICT', 'message': f'Username "{data["username"]}" is already taken.'}}, 409
        user.username = data['username']

    if 'email' in data:
        existing = User.query.filter(User.email == data['email'], User.id != user_id).first()
        if existing:
            return {'error': {'code': 'CONFLICT', 'message': f'Email "{data["email"]}" is already registered.'}}, 409
        user.email = data['email']

    if 'role' in data:
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'password' in data:
        user.set_password(data['password'])

    db.session.commit()
    logger.info(f"User updated: {user.username} (id={user_id})")
    return {'message': 'User updated successfully.', 'user': user.to_dict()}, 200


def delete_user(user_id: int) -> tuple[dict, int]:
    """Soft-delete a user by deactivating their account."""
    user = db.session.get(User, user_id)
    if not user:
        return {'error': {'code': 'NOT_FOUND', 'message': f'User with id {user_id} not found.'}}, 404

    user.is_active = False
    db.session.commit()
    logger.info(f"User deactivated: {user.username} (id={user_id})")
    return {'message': 'User deactivated successfully.'}, 200
