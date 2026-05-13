from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.project import Project


def get_token(client, username, password):
    """Login and return JWT token."""
    resp = client.post('/api/v1/auth/login', json={
        'username': username,
        'password': password,
    })
    return resp.get_json()['access_token']


def test_register_success():
    # Setup
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        client = app.test_client()

        # Test — register a new user
        resp = client.post('/api/v1/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'NewPass123!',
        })

        assert resp.status_code == 201
        data = resp.get_json()
        assert data['user']['username'] == 'newuser'
        assert data['user']['role'] == 'user'

        # Cleanup
        db.drop_all()


def test_login_success():
    # Setup
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        admin = User(username='admin', email='admin@test.com', role='admin')
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()

        client = app.test_client()

        # Test — login returns JWT tokens
        resp = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'Admin123!',
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['username'] == 'admin'

        # Cleanup
        db.drop_all()


def test_create_project_as_user_forbidden():
    # Setup
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        user = User(username='user', email='user@test.com', role='user')
        user.set_password('User123!')
        db.session.add(user)
        db.session.commit()

        client = app.test_client()
        token = get_token(client, 'user', 'User123!')

        # Test — regular user cannot create project
        resp = client.post('/api/v1/projects',
                           headers={'Authorization': f'Bearer {token}'},
                           json={'name': 'Forbidden Project'})

        assert resp.status_code == 403

        # Cleanup
        db.drop_all()


def test_update_project():
    # Setup
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        pm = User(username='pm', email='pm@test.com', role='project_manager')
        pm.set_password('Pm123!')
        db.session.add(pm)
        db.session.flush()

        project = Project(name='Test Project', description='A test project.',
                          status='active', owner_id=pm.id)
        db.session.add(project)
        db.session.flush()
        project.members.append(pm)
        db.session.commit()

        client = app.test_client()
        token = get_token(client, 'pm', 'Pm123!')

        # Test — PM can update own project
        resp = client.put(f'/api/v1/projects/{project.id}',
                          headers={'Authorization': f'Bearer {token}'},
                          json={'name': 'Updated Name', 'status': 'archived'})

        assert resp.status_code == 200
        assert resp.get_json()['project']['name'] == 'Updated Name'
        assert resp.get_json()['project']['status'] == 'archived'

        # Cleanup
        db.drop_all()
