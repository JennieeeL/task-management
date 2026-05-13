"""Integration tests for projects API endpoints."""
from tests.conftest import auth_header


class TestProjectsAPI:
    """Test /api/v1/projects endpoints."""

    def test_create_project_as_pm(self, client, pm_token):
        """POST /projects creates a project for PM."""
        resp = client.post('/api/v1/projects',
                           headers=auth_header(pm_token),
                           json={'name': 'New Project', 'description': 'Test desc'})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['project']['name'] == 'New Project'
        assert data['project']['status'] == 'active'

    def test_create_project_as_user_forbidden(self, client, user_token):
        """POST /projects returns 403 for regular user."""
        resp = client.post('/api/v1/projects',
                           headers=auth_header(user_token),
                           json={'name': 'Forbidden Project'})
        assert resp.status_code == 403

    def test_list_projects_admin_sees_all(self, client, admin_token, sample_project):
        """GET /projects returns all projects for admin."""
        resp = client.get('/api/v1/projects', headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert len(resp.get_json()['projects']) >= 1

    def test_list_projects_user_sees_assigned(self, client, user_token, sample_project):
        """GET /projects returns only assigned projects for user."""
        resp = client.get('/api/v1/projects', headers=auth_header(user_token))
        assert resp.status_code == 200
        projects = resp.get_json()['projects']
        assert len(projects) == 1
        assert projects[0]['name'] == 'Test Project'

    def test_get_project_with_members(self, client, pm_token, sample_project):
        """GET /projects/<id> returns project with members."""
        resp = client.get(f'/api/v1/projects/{sample_project.id}',
                          headers=auth_header(pm_token))
        assert resp.status_code == 200
        data = resp.get_json()['project']
        assert 'members' in data
        assert len(data['members']) == 2  # pm + user

    def test_get_project_user_not_member_forbidden(self, client, db, sample_project):
        """GET /projects/<id> returns 403 for non-member user."""
        from app.models.user import User
        outsider = User(username='outsider', email='out@test.com', role='user')
        outsider.set_password('Out12345!')
        db.session.add(outsider)
        db.session.commit()

        login_resp = client.post('/api/v1/auth/login', json={
            'username': 'outsider', 'password': 'Out12345!',
        })
        token = login_resp.get_json()['access_token']

        resp = client.get(f'/api/v1/projects/{sample_project.id}',
                          headers=auth_header(token))
        assert resp.status_code == 403

    def test_update_project(self, client, pm_token, sample_project):
        """PUT /projects/<id> updates project."""
        resp = client.put(f'/api/v1/projects/{sample_project.id}',
                          headers=auth_header(pm_token),
                          json={'name': 'Updated Name', 'status': 'archived'})
        assert resp.status_code == 200
        assert resp.get_json()['project']['name'] == 'Updated Name'
        assert resp.get_json()['project']['status'] == 'archived'

    def test_delete_project_admin_and_pm(self, client, pm_token, admin_token, sample_project, db):
        """DELETE /projects/<id> allowed for admin and PM (own projects)."""
        # PM can delete their own project
        resp = client.delete(f'/api/v1/projects/{sample_project.id}',
                             headers=auth_header(pm_token))
        assert resp.status_code == 200

        # Create another project for admin to delete
        from app.models.project import Project
        from app.models.user import User
        pm = User.query.filter_by(username='pm').first()
        project2 = Project(name='Admin Delete Test', owner_id=pm.id)
        db.session.add(project2)
        db.session.commit()

        resp = client.delete(f'/api/v1/projects/{project2.id}',
                             headers=auth_header(admin_token))
        assert resp.status_code == 200

    def test_add_member(self, client, pm_token, sample_project, admin_user):
        """POST /projects/<id>/members adds a member."""
        resp = client.post(f'/api/v1/projects/{sample_project.id}/members',
                           headers=auth_header(pm_token),
                           json={'user_id': admin_user.id})
        assert resp.status_code == 200
        members = resp.get_json()['project']['members']
        usernames = [m['username'] for m in members]
        assert 'admin' in usernames

    def test_add_duplicate_member(self, client, pm_token, sample_project, regular_user):
        """POST /projects/<id>/members rejects duplicate member."""
        resp = client.post(f'/api/v1/projects/{sample_project.id}/members',
                           headers=auth_header(pm_token),
                           json={'user_id': regular_user.id})
        assert resp.status_code == 409

    def test_remove_member(self, client, pm_token, sample_project, regular_user):
        """DELETE /projects/<id>/members/<user_id> removes a member."""
        resp = client.delete(
            f'/api/v1/projects/{sample_project.id}/members/{regular_user.id}',
            headers=auth_header(pm_token))
        assert resp.status_code == 200
