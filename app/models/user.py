"""User model with role-based access and password hashing."""
from datetime import datetime, timezone
from app.extensions import db, bcrypt


class User(db.Model):
    """User account with role-based permissions."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user', index=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    owned_projects = db.relationship('Project', backref='owner', lazy='dynamic',
                                     foreign_keys='Project.owner_id')
    assigned_tasks = db.relationship('Task', backref='assignee', lazy='dynamic',
                                     foreign_keys='Task.assignee_id')
    created_tasks = db.relationship('Task', backref='creator', lazy='dynamic',
                                    foreign_keys='Task.created_by_id')

    VALID_ROLES = ('admin', 'project_manager', 'user')

    def __init__(self, **kwargs):
        kwargs.setdefault('role', 'user')
        kwargs.setdefault('is_active', True)
        super().__init__(**kwargs)

    def set_password(self, password: str) -> None:
        """Hash and store the password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Serialize user to dictionary (excludes password)."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f'<User {self.username} ({self.role})>'
