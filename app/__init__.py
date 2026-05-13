import logging
from flask import Flask
from app.config import config_map
from app.extensions import db, bcrypt, jwt, cors, migrate, limiter
from app.middleware.error_handler import register_error_handlers
from app.api import register_blueprints


def create_app(config_name: str = 'default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map['default']))

    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    migrate.init_app(app, db)

    # Rate limiter
    if not app.config.get('RATELIMIT_ENABLED', True):
        app.config['RATELIMIT_STORAGE_URI'] = 'memory://'
    limiter.init_app(app)

    # Error handlers and blueprints
    register_error_handlers(app)
    register_blueprints(app)

    from app import models as _models  

    # Health check
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200

    return app
