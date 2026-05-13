from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task


def example():
    app = create_app()

    with app.app_context():
        db.create_all()

        # Check if already seeded
        if User.query.first():
            print("Database already seeded. Skipping.")
            return

        # --- Users ---
        admin = User(username='admin', email='admin@gmail.com', role='admin')
        admin.set_password('Admin123!')

        pm = User(username='pm', email='pm@gmail.com', role='project_manager')
        pm.set_password('Pm123!')

        user = User(username='user', email='user@gmail.com', role='user')
        user.set_password('User123!')

        db.session.add_all([admin, pm, user])
        db.session.flush()

        print(f"Created users: admin (id={admin.id}), pm (id={pm.id}), user (id={user.id})")

        # --- Projects ---
        project1 = Project(
            name='Project Genoa',
            description='Backend API development for the new platform.',
            status='active',
            owner_id=pm.id,
        )
        project2 = Project(
            name='Project Milan',
            description='Infrastructure monitoring and alerting system.',
            status='active',
            owner_id=pm.id,
        )

        db.session.add_all([project1, project2])
        db.session.flush()

        # Assign members
        project1.members.extend([pm, user])
        project2.members.extend([pm, user])

        print(f"Created projects: {project1.name} (id={project1.id}), {project2.name} (id={project2.id})")

        # --- Tasks ---
        tasks = [
            Task(
                title='Design database schema',
                description='Create ER diagram and define all tables with relationships.',
                status='done',
                project_id=project1.id,
                assignee_id=user.id,
                created_by_id=pm.id,
                due_date=date.today() - timedelta(days=5),
            ),
            Task(
                title='Implement JWT authentication',
                description='Set up Flask-JWT-Extended with access and refresh tokens.',
                status='in_progress',
                project_id=project1.id,
                assignee_id=user.id,
                created_by_id=pm.id,
                due_date=date.today() + timedelta(days=2),
            ),
            Task(
                title='Set up Prometheus metrics',
                description='Integrate Prometheus client and expose /metrics endpoint.',
                status='todo',
                project_id=project2.id,
                assignee_id=user.id,
                created_by_id=pm.id,
                due_date=date.today() + timedelta(days=10),
            ),
            Task(
                title='Configure alerting rules',
                description='Define alerting rules for CPU, memory, and disk usage.',
                status='todo',
                project_id=project2.id,
                assignee_id=None,
                created_by_id=pm.id,
                due_date=date.today() + timedelta(days=14),
            ),
        ]

        db.session.add_all(tasks)
        db.session.commit()

        print(f"Created {len(tasks)} tasks.")
        print("\nDummy data created successfully!")
        print("\nLogin credentials:")
        print("  Admin:           admin / Admin123!")
        print("  Project Manager: pm    / Pm123!")
        print("  User:            user  / User123!")


if __name__ == '__main__':
    example()
