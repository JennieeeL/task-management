"""Authentication and authorization middleware."""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt


def role_required(*allowed_roles: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role', '')
            if user_role not in allowed_roles:
                return jsonify({
                    'error': {
                        'code': 'FORBIDDEN',
                        'message': f'Access denied. Required role: {", ".join(allowed_roles)}.',
                    }
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
