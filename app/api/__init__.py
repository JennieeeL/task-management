"""Register all API blueprints."""
from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Register all API blueprints with the app."""
    from app.api.auth import auth_bp
    from app.api.users import users_bp
    from app.api.projects import projects_bp
    from app.api.tasks import tasks_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(projects_bp, url_prefix='/api/v1/projects')
    app.register_blueprint(tasks_bp, url_prefix='/api/v1/tasks')
