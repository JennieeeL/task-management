"""Global error handlers for consistent API error responses."""
import logging
from flask import Flask, jsonify
from marshmallow import ValidationError

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask):
    """Register error handlers on the Flask app."""

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Input validation failed.',
                'details': e.messages,
            }
        }), 422

    @app.errorhandler(400)
    def handle_bad_request(e):
        return jsonify({
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(e.description) if hasattr(e, 'description') else 'Bad request.',
            }
        }), 400

    @app.errorhandler(401)
    def handle_unauthorized(e):
        return jsonify({
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Authentication required.',
            }
        }), 401

    @app.errorhandler(403)
    def handle_forbidden(e):
        return jsonify({
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access this resource.',
            }
        }), 403

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({
            'error': {
                'code': 'NOT_FOUND',
                'message': 'The requested resource was not found.',
            }
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({
            'error': {
                'code': 'METHOD_NOT_ALLOWED',
                'message': 'This HTTP method is not allowed for this endpoint.',
            }
        }), 405

    @app.errorhandler(429)
    def handle_rate_limit(e):
        return jsonify({
            'error': {
                'code': 'RATE_LIMITED',
                'message': 'Too many requests. Please try again later.',
            }
        }), 429

    @app.errorhandler(500)
    def handle_internal_error(e):
        logger.exception("Internal server error")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred.',
            }
        }), 500
