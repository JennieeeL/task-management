"""Integration tests for users API endpoints."""
from tests.conftest import auth_header


class TestUsersAPI:
    """Test /api/v1/users endpoints (admin only)."""

    def test_list_users_as_admin(self, client, admin_token, pm_user, regular_user):
        """GET /users returns all users for admin."""
        resp = client.get('/api/v1/users', headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['users']) == 3  # admin + pm + user
        assert 'pagination' in data

    def test_list_users_as_regular_user_forbidden(self, client, user_token):
        """GET /users returns 403 for non-admin."""
        resp = client.get('/api/v1/users', headers=auth_header(user_token))
        assert resp.status_code == 403

    def test_list_users_as_pm_forbidden(self, client, pm_token):
        """GET /users returns 403 for PM."""
        resp = client.get('/api/v1/users', headers=auth_header(pm_token))
        assert resp.status_code == 403

    def test_get_user_as_admin(self, client, admin_token, regular_user):
        """GET /users/<id> returns user details for admin."""
        resp = client.get(f'/api/v1/users/{regular_user.id}',
                          headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.get_json()['user']['username'] == 'user'

    def test_get_user_not_found(self, client, admin_token):
        """GET /users/<id> returns 404 for non-existent user."""
        resp = client.get('/api/v1/users/9999', headers=auth_header(admin_token))
        assert resp.status_code == 404

    def test_update_user_role(self, client, admin_token, regular_user):
        """PUT /users/<id> updates user role."""
        resp = client.put(f'/api/v1/users/{regular_user.id}',
                          headers=auth_header(admin_token),
                          json={'role': 'project_manager'})
        assert resp.status_code == 200
        assert resp.get_json()['user']['role'] == 'project_manager'

    def test_update_user_duplicate_username(self, client, admin_token, regular_user, admin_user):
        """PUT /users/<id> rejects duplicate username."""
        resp = client.put(f'/api/v1/users/{regular_user.id}',
                          headers=auth_header(admin_token),
                          json={'username': 'admin'})
        assert resp.status_code == 409

    def test_delete_user_soft_deletes(self, client, admin_token, regular_user):
        """DELETE /users/<id> deactivates the user."""
        resp = client.delete(f'/api/v1/users/{regular_user.id}',
                             headers=auth_header(admin_token))
        assert resp.status_code == 200

        # Verify user is deactivated
        resp = client.get(f'/api/v1/users/{regular_user.id}',
                          headers=auth_header(admin_token))
        assert resp.get_json()['user']['is_active'] is False

    def test_pagination(self, client, admin_token, pm_user, regular_user):
        """GET /users supports pagination."""
        resp = client.get('/api/v1/users?page=1&per_page=1',
                          headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['users']) == 1
        assert data['pagination']['total'] == 3
        assert data['pagination']['pages'] == 3
        assert data['pagination']['has_next'] is True
