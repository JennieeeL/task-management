"""Project model with member associations."""
from datetime import datetime, timezone
from app.extensions import db

project_members = db.Table(
    'project_members',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=lambda: datetime.now(timezone.utc)),
)


class Project(db.Model):
    """Project that contains tasks and members."""

    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active', index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    members = db.relationship('User', secondary=project_members, backref=db.backref('projects', lazy='dynamic'))
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade='all, delete-orphan')

    VALID_STATUSES = ('active', 'archived')

    def to_dict(self, include_members: bool = False) -> dict:
        """Serialize project to dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'owner_id': self.owner_id,
            'owner': self.owner.to_dict() if self.owner else None,
            'task_count': self.tasks.count(),
            'member_count': len(self.members),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_members:
            data['members'] = [m.to_dict() for m in self.members]
        return data

    def __repr__(self) -> str:
        return f'<Project {self.name}>'
