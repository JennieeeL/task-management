"""Integration tests for auth API endpoints."""
from tests.conftest import auth_header


class TestAuthAPI:
    """Test /api/v1/auth endpoints."""

    def test_register_success(self, client):
        """POST /auth/register creates a new user."""
        resp = client.post('/api/v1/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'NewPass123!',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['user']['username'] == 'newuser'
        assert data['user']['role'] == 'user'

    def test_register_validation_short_password(self, client):
        """POST /auth/register rejects short password."""
        resp = client.post('/api/v1/auth/register', json={
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'short',
        })
        assert resp.status_code == 422

    def test_register_validation_invalid_email(self, client):
        """POST /auth/register rejects invalid email."""
        resp = client.post('/api/v1/auth/register', json={
            'username': 'newuser',
            'email': 'not-an-email',
            'password': 'ValidPass123!',
        })
        assert resp.status_code == 422

    def test_register_duplicate_username(self, client, admin_user):
        """POST /auth/register rejects duplicate username."""
        resp = client.post('/api/v1/auth/register', json={
            'username': 'admin',
            'email': 'other@test.com',
            'password': 'ValidPass123!',
        })
        assert resp.status_code == 409

    def test_login_success(self, client, admin_user):
        """POST /auth/login returns JWT tokens."""
        resp = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'Admin123!',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['username'] == 'admin'

    def test_login_wrong_password(self, client, admin_user):
        """POST /auth/login rejects wrong password."""
        resp = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'WrongPass!',
        })
        assert resp.status_code == 401

    def test_me_authenticated(self, client, admin_token):
        """GET /auth/me returns current user profile."""
        resp = client.get('/api/v1/auth/me', headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.get_json()['user']['username'] == 'admin'

    def test_me_unauthenticated(self, client):
        """GET /auth/me without token returns 401."""
        resp = client.get('/api/v1/auth/me')
        assert resp.status_code == 401

    def test_refresh_token(self, client, admin_user):
        """POST /auth/refresh returns a new access token."""
        login_resp = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'Admin123!',
        })
        refresh_token = login_resp.get_json()['refresh_token']

        resp = client.post('/api/v1/auth/refresh',
                           headers={'Authorization': f'Bearer {refresh_token}'})
        assert resp.status_code == 200
        assert 'access_token' in resp.get_json()
