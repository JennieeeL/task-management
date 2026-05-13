"""Pytest fixtures for unit and integration tests."""
import pytest
from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task


@pytest.fixture(scope='session')
def app():
    """Create a Flask app configured for testing."""
    app = create_app('testing')
    yield app


@pytest.fixture(scope='function')
def db(app):
    """Create fresh database tables for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    """Flask test client with a clean database."""
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture()
def admin_user(db):
    """Create an admin user."""
    user = User(username='admin', email='admin@test.com', role='admin')
    user.set_password('Admin123!')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def pm_user(db):
    """Create a project manager user."""
    user = User(username='pm', email='pm@test.com', role='project_manager')
    user.set_password('Pm123!')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def regular_user(db):
    """Create a regular user."""
    user = User(username='user', email='user@test.com', role='user')
    user.set_password('User123!')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def admin_token(client, admin_user):
    """Get a JWT access token for the admin user."""
    resp = client.post('/api/v1/auth/login', json={
        'username': 'admin',
        'password': 'Admin123!',
    })
    return resp.get_json()['access_token']


@pytest.fixture()
def pm_token(client, pm_user):
    """Get a JWT access token for the PM user."""
    resp = client.post('/api/v1/auth/login', json={
        'username': 'pm',
        'password': 'Pm123!',
    })
    return resp.get_json()['access_token']


@pytest.fixture()
def user_token(client, regular_user):
    """Get a JWT access token for the regular user."""
    resp = client.post('/api/v1/auth/login', json={
        'username': 'user',
        'password': 'User123!',
    })
    return resp.get_json()['access_token']


@pytest.fixture()
def sample_project(db, pm_user, regular_user):
    """Create a sample project owned by PM with regular user as member."""
    project = Project(
        name='Test Project',
        description='A test project.',
        status='active',
        owner_id=pm_user.id,
    )
    db.session.add(project)
    db.session.flush()
    project.members.extend([pm_user, regular_user])
    db.session.commit()
    return project


@pytest.fixture()
def sample_task(db, sample_project, pm_user, regular_user):
    """Create a sample task assigned to regular user."""
    task = Task(
        title='Test Task',
        description='A test task.',
        status='todo',
        project_id=sample_project.id,
        assignee_id=regular_user.id,
        created_by_id=pm_user.id,
    )
    db.session.add(task)
    db.session.commit()
    return task


def auth_header(token: str) -> dict:
    """Build Authorization header from a JWT token."""
    return {'Authorization': f'Bearer {token}'}
