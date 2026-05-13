# Task Management API

Production-ready REST API for task management with role-based access control (RBAC), built with Flask, MariaDB, and Redis.

## Architecture

```
task-management-api/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # App configuration
│   ├── extensions.py        # Flask extension instances
│   ├── api/                 # Route blueprints
│   │   ├── auth.py          # Register, login, refresh, me
│   │   ├── users.py         # User CRUD (admin only)
│   │   ├── projects.py      # Project CRUD + member mgmt
│   │   └── tasks.py         # Task CRUD + filtering
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py          # User with bcrypt passwords
│   │   ├── project.py       # Project with M2M members
│   │   └── task.py          # Task with composite indexes
│   ├── schemas/             # Marshmallow validation
│   ├── services/            # Business logic layer
│   ├── middleware/          # Auth decorators, error handlers
│   └── utils/               # Pagination, Redis cache
├── tests/
│   └── test_simple.py       # Standalone integration tests
├── docker-compose.yml       # App + MariaDB + Redis
├── Dockerfile               # Python image with Gunicorn
├── example.py               # Seed data script
└── wsgi.py                  # Gunicorn entrypoint
```

## Roles & Permissions

| Action | Admin | Project Manager | User |
|---|:---:|:---:|:---:|
| Manage users | ✅ | ❌ | ❌ |
| View all projects | ✅ | Own only | Assigned only |
| Create/update projects | ✅ | ✅ | ❌ |
| Delete projects | ✅ | Own only | ❌ |
| Assign project members | ✅ | Own projects | ❌ |
| Create/assign tasks | ✅ | Own projects | ❌ |
| Update tasks (all fields) | ✅ | Own projects | ❌ |
| Update own task status | ✅ | ✅ | ✅ |
| Delete tasks | ✅ | Own projects | ❌ |

## Quick Start

### Docker (recommended)

```bash
# Start all services
docker compose up --build -d

# Seed sample data
docker compose exec app python example.py

# Run tests
docker compose exec app python -m pytest tests/ -v
```


## API Endpoints

Base URL: `http://localhost:5000/api/v1`

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login, get JWT tokens | No |
| POST | `/auth/refresh` | Refresh access token | Refresh token |
| GET | `/auth/me` | Get current user profile | Yes |

### Users (Admin only)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users` | List all users (paginated) |
| GET | `/users/:id` | Get user details |
| PUT | `/users/:id` | Update user |
| DELETE | `/users/:id` | Deactivate user |

### Projects

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| GET | `/projects` | List projects (role-filtered) | All |
| POST | `/projects` | Create project | Admin, PM |
| GET | `/projects/:id` | Get project with members | All (access-controlled) |
| PUT | `/projects/:id` | Update project | Admin, PM (own) |
| DELETE | `/projects/:id` | Delete project | Admin, PM (own) |
| POST | `/projects/:id/members` | Add member | Admin, PM (own) |
| DELETE | `/projects/:id/members/:uid` | Remove member | Admin, PM (own) |

### Tasks

| Method | Endpoint | Description | Roles |
|---|---|---|---|
| GET | `/tasks` | List tasks (filtered, paginated) | All (role-scoped) |
| POST | `/tasks` | Create task | Admin, PM |
| GET | `/tasks/:id` | Get task details | All (access-controlled) |
| PUT | `/tasks/:id` | Update task | Admin, PM, User (status only) |
| DELETE | `/tasks/:id` | Delete task | Admin, PM |

**Task filters** (query params): `status`, `assignee_id`, `project_id`, `sort_by`, `sort_order`, `page`, `per_page`

### Health Check

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health check |

## Usage Examples

### Register & Login

```bash
# Register
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com", "password": "SecurePass123!"}'

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123!"}'

# Use the access_token from login response:
export TOKEN="eyJ..."
```

### Projects

```bash
# Create project (admin/PM)
curl -X POST http://localhost:5000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Backend API", "description": "New backend service"}'

# Add member to project
curl -X POST http://localhost:5000/api/v1/projects/1/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 3}'
```

### Tasks

```bash
# Create task
curl -X POST http://localhost:5000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Design DB schema", "project_id": 1, "assignee_id": 3}'

# List tasks with filters
curl "http://localhost:5000/api/v1/tasks?status=todo&sort_by=due_date&page=1&per_page=10" \
  -H "Authorization: Bearer $TOKEN"

# User updates own task status
curl -X PUT http://localhost:5000/api/v1/tasks/1 \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

## Seed Data

After running `python example.py`, use these credentials:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin123!` |
| Project Manager | `pm` | `Pm123!` |
| User | `user` | `User123!` |

## Design Decisions

### Performance
- **Redis caching** on list endpoints with pattern-based invalidation
- **Composite indexes** on `(project_id, status)` and `(assignee_id, status)` for common query patterns
- **Pagination** on all list endpoints (max 100 per page)

### Security
- **Bcrypt** password hashing
- **JWT** with short-lived access tokens (15min) and long-lived refresh tokens (30d)
- **Rate limiting** — 5/min on register, 10/min on login, 200/min global
- **Input validation** via Marshmallow schemas on all endpoints
- **Soft delete** for users (deactivation, not data loss)

### Architecture
- **Service layer** separates business logic from route handlers
- **Blueprint-based** routing for modular API organization
- **Consistent error responses** with error codes via global error handlers
- **Graceful Redis fallback** — app works without Redis (caching disabled)

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing
```


