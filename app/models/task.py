"""Task model with status and relationships."""
from datetime import datetime, timezone, date
from app.extensions import db


class Task(db.Model):
    """Task belonging to a project, optionally assigned to a user."""

    __tablename__ = 'tasks'
    __table_args__ = (
        db.Index('ix_tasks_project_status', 'project_id', 'status'),
        db.Index('ix_tasks_assignee_status', 'assignee_id', 'status'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='todo', index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    VALID_STATUSES = ('todo', 'in_progress', 'review', 'done')
    def __init__(self, **kwargs):
        kwargs.setdefault('status', 'todo')
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        """Serialize task to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'assignee_id': self.assignee_id,
            'assignee': self.assignee.to_dict() if self.assignee else None,
            'created_by_id': self.created_by_id,
            'creator': self.creator.to_dict() if self.creator else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f'<Task {self.title} ({self.status})>'
