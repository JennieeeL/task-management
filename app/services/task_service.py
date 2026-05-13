import logging
from sqlalchemy.orm import joinedload
from sqlalchemy import asc, desc
from app.extensions import db
from app.models.task import Task
from app.models.project import Project
from app.models.user import User
from app.utils.pagination import paginate_query
from app.utils.cache import cache_get, cache_set, cache_delete_pattern, make_cache_key

logger = logging.getLogger(__name__)

TASK_LIST_TTL = 300    
TASK_DETAIL_TTL = 600  


def list_tasks(current_user_id: int, current_role: str,
               filters: dict):
    page = filters.get('page', 1)
    per_page = filters.get('per_page', 20)
    sort_by = filters.get('sort_by', 'created_at')
    sort_order = filters.get('sort_order', 'desc')

    cache_key = f"tasks:list:{make_cache_key(current_user_id, current_role, str(sorted(filters.items())))}"
    cached = cache_get(cache_key)
    if cached:
        return cached, 200

    query = Task.query.options(
        joinedload(Task.assignee),
        joinedload(Task.creator),
        joinedload(Task.project),
    )

    # Role-based scoping
    if current_role == 'user':
        query = query.filter(Task.assignee_id == current_user_id)
    elif current_role == 'project_manager':
        pm_project_ids = db.session.query(Project.id).filter_by(owner_id=current_user_id).scalar_subquery()
        query = query.filter(Task.project_id.in_(pm_project_ids))

    # Apply filters
    if filters.get('status'):
        query = query.filter(Task.status == filters['status'])
    if filters.get('assignee_id'):
        query = query.filter(Task.assignee_id == filters['assignee_id'])
    if filters.get('project_id'):
        query = query.filter(Task.project_id == filters['project_id'])

    # Sorting
    sort_column = getattr(Task, sort_by, Task.created_at)
    order_func = desc if sort_order == 'desc' else asc
    query = query.order_by(order_func(sort_column))

    result = paginate_query(query, page=page, per_page=per_page)
    response = {
        'tasks': [t.to_dict() for t in result['items']],
        'pagination': result['pagination'],
    }
    cache_set(cache_key, response, ttl=TASK_LIST_TTL)
    return response, 200


def create_task(data: dict, current_user_id: int,
                current_role: str):
    """Create a new task in a project."""
    project = db.session.get(Project, data['project_id'])
    if not project:
        return {'error': {'code': 'NOT_FOUND', 'message': f'Project with id {data["project_id"]} not found.'}}, 404

    if current_role == 'project_manager' and project.owner_id != current_user_id:
        return {'error': {'code': 'FORBIDDEN', 'message': 'You can only create tasks in projects you own.'}}, 403

    if data.get('assignee_id'):
        assignee = db.session.get(User, data['assignee_id'])
        if not assignee:
            return {'error': {'code': 'NOT_FOUND', 'message': f'Assignee with id {data["assignee_id"]} not found.'}}, 404

    task = Task(
        title=data['title'],
        description=data.get('description'),
        status=data.get('status', 'todo'),
        project_id=data['project_id'],
        assignee_id=data.get('assignee_id'),
        created_by_id=current_user_id,
        due_date=data.get('due_date'),
    )
    db.session.add(task)
    db.session.commit()
    cache_delete_pattern("tasks:*")
    logger.info(f"Task created: {task.title} (id={task.id}, project={project.name})")
    return {'message': 'Task created successfully.', 'task': task.to_dict()}, 201


def get_task(task_id: int, current_user_id: int,
             current_role: str):
    """Get a single task with access control."""
    task = db.session.query(Task).options(
        joinedload(Task.assignee),
        joinedload(Task.creator),
        joinedload(Task.project),
    ).get(task_id)

    if not task:
        return {'error': {'code': 'NOT_FOUND', 'message': f'Task with id {task_id} not found.'}}, 404

    if current_role == 'user' and task.assignee_id != current_user_id:
        return {'error': {'code': 'FORBIDDEN', 'message': 'You can only view tasks assigned to you.'}}, 403
    elif current_role == 'project_manager' and task.project.owner_id != current_user_id:
        return {'error': {'code': 'FORBIDDEN', 'message': 'You can only view tasks in projects you own.'}}, 403

    return {'task': task.to_dict()}, 200


def update_task(task_id: int, data: dict, current_user_id: int,
                current_role: str):
    """Update a task with role-based field restrictions."""
    task = db.session.get(Task, task_id)
    if not task:
        return {'error': {'code': 'NOT_FOUND', 'message': f'Task with id {task_id} not found.'}}, 404

    if current_role == 'user':
        if task.assignee_id != current_user_id:
            return {'error': {'code': 'FORBIDDEN', 'message': 'You can only update tasks assigned to you.'}}, 403
        allowed_fields = {'status'}
        extra_fields = set(data.keys()) - allowed_fields
        if extra_fields:
            return {'error': {
                'code': 'FORBIDDEN',
                'message': f'Users can only update: {", ".join(allowed_fields)}. Cannot update: {", ".join(extra_fields)}',
            }}, 403
    elif current_role == 'project_manager':
        if task.project.owner_id != current_user_id:
            return {'error': {'code': 'FORBIDDEN', 'message': 'You can only update tasks in projects you own.'}}, 403

    if 'assignee_id' in data and data['assignee_id'] is not None:
        assignee = db.session.get(User, data['assignee_id'])
        if not assignee:
            return {'error': {'code': 'NOT_FOUND', 'message': f'Assignee with id {data["assignee_id"]} not found.'}}, 404

    for field in ('title', 'description', 'status', 'assignee_id', 'due_date'):
        if field in data:
            setattr(task, field, data[field])

    db.session.commit()
    cache_delete_pattern("tasks:*")
    logger.info(f"Task updated: {task.title} (id={task_id})")
    return {'message': 'Task updated successfully.', 'task': task.to_dict()}, 200


def delete_task(task_id: int, current_user_id: int,
                current_role: str):
    """Delete a task."""
    task = db.session.get(Task, task_id)
    if not task:
        return {'error': {'code': 'NOT_FOUND', 'message': f'Task with id {task_id} not found.'}}, 404

    if current_role == 'project_manager' and task.project.owner_id != current_user_id:
        return {'error': {'code': 'FORBIDDEN', 'message': 'You can only delete tasks in projects you own.'}}, 403

    db.session.delete(task)
    db.session.commit()
    cache_delete_pattern("tasks:*")
    logger.info(f"Task deleted: {task.title} (id={task_id})")
    return {'message': 'Task deleted successfully.'}, 200
