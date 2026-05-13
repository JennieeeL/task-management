"""Integration tests for tasks API endpoints."""
from tests.conftest import auth_header


class TestTasksAPI:
    """Test /api/v1/tasks endpoints."""

    def test_create_task_as_pm(self, client, pm_token, sample_project, regular_user):
        """POST /tasks creates a task for PM."""
        resp = client.post('/api/v1/tasks',
                           headers=auth_header(pm_token),
                           json={
                               'title': 'New Task',
                               'description': 'Task description',
                               'project_id': sample_project.id,
                               'assignee_id': regular_user.id,
                           })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['task']['title'] == 'New Task'
        assert data['task']['status'] == 'todo'

    def test_create_task_as_user_forbidden(self, client, user_token, sample_project):
        """POST /tasks returns 403 for regular user."""
        resp = client.post('/api/v1/tasks',
                           headers=auth_header(user_token),
                           json={'title': 'Forbidden', 'project_id': sample_project.id})
        assert resp.status_code == 403

    def test_create_task_invalid_project(self, client, pm_token):
        """POST /tasks returns 404 for non-existent project."""
        resp = client.post('/api/v1/tasks',
                           headers=auth_header(pm_token),
                           json={'title': 'Bad Task', 'project_id': 9999})
        assert resp.status_code == 404

    def test_list_tasks_admin_sees_all(self, client, admin_token, sample_task):
        """GET /tasks returns all tasks for admin."""
        resp = client.get('/api/v1/tasks', headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert len(resp.get_json()['tasks']) >= 1

    def test_list_tasks_user_sees_assigned_only(self, client, pm_token, user_token,
                                                 sample_project, regular_user, pm_user, db):
        """GET /tasks returns only assigned tasks for regular user."""
        from app.models.task import Task

        # Create a task NOT assigned to regular user
        unassigned = Task(
            title='PM Only Task', project_id=sample_project.id,
            created_by_id=pm_user.id, assignee_id=pm_user.id,
        )
        # Create a task assigned to regular user
        assigned = Task(
            title='User Task', project_id=sample_project.id,
            created_by_id=pm_user.id, assignee_id=regular_user.id,
        )
        db.session.add_all([unassigned, assigned])
        db.session.commit()

        resp = client.get('/api/v1/tasks', headers=auth_header(user_token))
        assert resp.status_code == 200
        tasks = resp.get_json()['tasks']
        # All tasks should be assigned to regular user
        for t in tasks:
            assert t['assignee_id'] == regular_user.id

    def test_list_tasks_filter_by_status(self, client, admin_token, sample_task):
        """GET /tasks?status=todo filters by status."""
        resp = client.get('/api/v1/tasks?status=todo',
                          headers=auth_header(admin_token))
        assert resp.status_code == 200
        for t in resp.get_json()['tasks']:
            assert t['status'] == 'todo'

    def test_list_tasks_pagination(self, client, pm_token, sample_project, pm_user, db):
        """GET /tasks supports pagination."""
        from app.models.task import Task
        for i in range(5):
            db.session.add(Task(
                title=f'Task {i}', project_id=sample_project.id,
                created_by_id=pm_user.id,
            ))
        db.session.commit()

        resp = client.get('/api/v1/tasks?page=1&per_page=2',
                          headers=auth_header(pm_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['tasks']) == 2
        assert data['pagination']['total'] == 5
        assert data['pagination']['has_next'] is True

    def test_get_task(self, client, pm_token, sample_task):
        """GET /tasks/<id> returns task details."""
        resp = client.get(f'/api/v1/tasks/{sample_task.id}',
                          headers=auth_header(pm_token))
        assert resp.status_code == 200
        assert resp.get_json()['task']['title'] == 'Test Task'

    def test_get_task_not_found(self, client, admin_token):
        """GET /tasks/<id> returns 404 for non-existent task."""
        resp = client.get('/api/v1/tasks/9999', headers=auth_header(admin_token))
        assert resp.status_code == 404

    def test_update_task_as_pm(self, client, pm_token, sample_task):
        """PUT /tasks/<id> allows PM to update any field."""
        resp = client.put(f'/api/v1/tasks/{sample_task.id}',
                          headers=auth_header(pm_token),
                          json={'title': 'Updated Title'})
        assert resp.status_code == 200
        data = resp.get_json()['task']
        assert data['title'] == 'Updated Title'

    def test_update_task_user_can_update_status_only(self, client, user_token, sample_task):
        """PUT /tasks/<id> allows user to update only status."""
        resp = client.put(f'/api/v1/tasks/{sample_task.id}',
                          headers=auth_header(user_token),
                          json={'status': 'in_progress'})
        assert resp.status_code == 200
        assert resp.get_json()['task']['status'] == 'in_progress'

    def test_update_task_user_cannot_update_title(self, client, user_token, sample_task):
        """PUT /tasks/<id> rejects user updating non-status fields."""
        resp = client.put(f'/api/v1/tasks/{sample_task.id}',
                          headers=auth_header(user_token),
                          json={'title': 'Hacked Title'})
        assert resp.status_code == 403

    def test_update_task_user_cannot_update_other_users_task(self, client, db,
                                                              sample_project, pm_user):
        """PUT /tasks/<id> rejects user updating tasks not assigned to them."""
        from app.models.task import Task
        from app.models.user import User

        other = User(username='other', email='other@test.com', role='user')
        other.set_password('Other123!')
        db.session.add(other)
        db.session.flush()

        task = Task(title='Other Task', project_id=sample_project.id,
                    created_by_id=pm_user.id, assignee_id=pm_user.id)
        db.session.add(task)
        db.session.commit()

        login_resp = client.post('/api/v1/auth/login', json={
            'username': 'other', 'password': 'Other123!',
        })
        token = login_resp.get_json()['access_token']

        resp = client.put(f'/api/v1/tasks/{task.id}',
                          headers=auth_header(token),
                          json={'status': 'done'})
        assert resp.status_code == 403

    def test_delete_task_as_pm(self, client, pm_token, sample_task):
        """DELETE /tasks/<id> allows PM to delete."""
        resp = client.delete(f'/api/v1/tasks/{sample_task.id}',
                             headers=auth_header(pm_token))
        assert resp.status_code == 200

        # Verify deleted
        resp = client.get(f'/api/v1/tasks/{sample_task.id}',
                          headers=auth_header(pm_token))
        assert resp.status_code == 404

    def test_delete_task_as_user_forbidden(self, client, user_token, sample_task):
        """DELETE /tasks/<id> returns 403 for regular user."""
        resp = client.delete(f'/api/v1/tasks/{sample_task.id}',
                             headers=auth_header(user_token))
        assert resp.status_code == 403
