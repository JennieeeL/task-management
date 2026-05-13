"""Project management service."""
import logging
from app.extensions import db
from app.models.user import User
from app.models.project import Project
from app.utils.pagination import paginate_query
from app.utils.cache import cache_get, cache_set, cache_delete_pattern

logger = logging.getLogger(__name__)

PROJECT_CACHE_TTL = 600   
PROJECT_LIST_TTL = 300    


def list_projects(current_user_id: int, current_role: str,
                  page: int = 1, per_page: int = 20):
    """List projects based on user role."""
    cache_key = f"projects:list:{current_user_id}:{current_role}:{page}:{per_page}"
    cached = cache_get(cache_key)
    if cached:
        return cached, 200

    if current_role == 'admin':
        query = Project.query
    elif current_role == 'project_manager':
        query = Project.query.filter_by(owner_id=current_user_id)
    else:
        user = db.session.get(User, current_user_id)
        query = user.projects if user else Project.query.filter(False)

    query = query.order_by(Project.created_at.desc())
    result = paginate_query(query, page=page, per_page=per_page)
    response = {
        'projects': [p.to_dict() for p in result['items']],
        'pagination': result['pagination'],
    }
    cache_set(cache_key, response, ttl=PROJECT_LIST_TTL)
    return response, 200


def create_project(name: str, description: str, owner_id: int,
                   status: str = 'active'):
    """Create a new project."""
    project = Project(name=name, description=description, owner_id=owner_id, status=status)
    db.session.add(project)
    db.session.commit()
    cache_delete_pattern("projects:*")
    logger.info(f"Project created: {name} (id={project.id}, owner={owner_id})")
    return {'message': 'Project created successfully.', 'project': project.to_dict()}, 201


def get_project(project_id: int, current_user_id: int,
                current_role: str):
    """Get a single project with access control."""
    project = db.session.get(Project, project_id)
    if not project:
        return {'error': {'code': 'NOT_FOUND', 'message': f'Project with id {project_id} not found.'}}, 404

    if current_role == 'user':
        user = db.session.get(User, current_user_id)
        if user not in project.members:
            return {'error': {'code': 'FORBIDDEN', 'message': 'You are not a member of this project.'}}, 403
    elif current_role == 'project_manager' and project.owner_id != current_user_id:
        return {'error': {'code': 'FORBIDDEN', 'message': 'You can only view projects you own.'}}, 403

    return {'project': project.to_dict(include_members=True)}, 200


def update_project(project_id: int, data: dict, current_user_id: int,
                   current_role: str):
    """Update a project."""
    project = db.session.get(Project, project_id)
    if not project:
        return {'error': {'code': 'NOT_FOUND', 'message': f'Project with id {project_id} not found.'}}, 404

    if current_role == 'project_manager' and project.owner_id != current_user_id:
        return {'error': {'code': 'FORBIDDEN', 'message': 'You can only update projects you own.'}}, 403

    if 'name' in data:
        project.name = data['name']
    if 'description' in data:
        project.description = data['description']
    if 'status' in data:
        project.status = data['status']

    db.session.commit()
    cache_delete_pattern("projects:*")
    logger.info(f"Project updated: {project.name} (id={project_id})")
    return {'message': 'Project updated successfully.', 'project': project.to_dict()}, 200


def delete_project(project_id: int, current_user_id: int, current_role: str):
    """Delete a project (admin and PM only)."""
    project = db.session.get(Project, project_id)
    if not project:
        return {'error': {'code': 'NOT_FOUND', 'message': f'Project with id {project_id} not found.'}}, 404

    if current_role == 'project_manager' and project.owner_id != current_user_id:
        return {'error': {'code': 'FORBIDDEN', 'message': 'You can only delete projects you own.'}}, 403

    db.session.delete(project)
    db.session.commit()
    cache_delete_pattern("projects:*")
    cache_delete_pattern("tasks:*")
    logger.info(f"Project deleted: {project.name} (id={project_id})")
    return {'message': 'Project deleted successfully.'}, 200


def add_member(project_id: int, user_id: int, current_user_id: int,
               current_role: str):
    """Add a user to a project."""
    project = db.session.get(Project, project_id)
    if not project:
        return {'error': {'code': 'NOT_FOUND', 'message': f'Project with id {project_id} not found.'}}, 404

    if current_role == 'project_manager' and project.owner_id != current_user_id:
        return {'error': {'code': 'FORBIDDEN', 'message': 'You can only manage members of projects you own.'}}, 403

    user = db.session.get(User, user_id)
    if not user:
        return {'error': {'code': 'NOT_FOUND', 'message': f'User with id {user_id} not found.'}}, 404

    if user in project.members:
        return {'error': {'code': 'CONFLICT', 'message': f'User "{user.username}" is already a member.'}}, 409

    project.members.append(user)
    db.session.commit()
    cache_delete_pattern("projects:*")
    logger.info(f"Member added: user={user.username}, project={project.name}")
    return {
        'message': f'User "{user.username}" added to project "{project.name}".',
        'project': project.to_dict(include_members=True),
    }, 200


def remove_member(project_id: int, user_id: int, current_user_id: int,
                  current_role: str):
    """Remove a user from a project."""
    project = db.session.get(Project, project_id)
    if not project:
        return {'error': {'code': 'NOT_FOUND', 'message': f'Project with id {project_id} not found.'}}, 404

    if current_role == 'project_manager' and project.owner_id != current_user_id:
        return {'error': {'code': 'FORBIDDEN', 'message': 'You can only manage members of projects you own.'}}, 403

    user = db.session.get(User, user_id)
    if not user:
        return {'error': {'code': 'NOT_FOUND', 'message': f'User with id {user_id} not found.'}}, 404

    if user not in project.members:
        return {'error': {'code': 'NOT_FOUND', 'message': f'User "{user.username}" is not a member.'}}, 404

    project.members.remove(user)
    db.session.commit()
    cache_delete_pattern("projects:*")
    logger.info(f"Member removed: user={user.username}, project={project.name}")
    return {'message': f'User "{user.username}" removed from project "{project.name}".'}, 200
