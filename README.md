# TalentHub – FastAPI Campus Placement Management System

## Stack
- FastAPI + Uvicorn (backend)
- SQLAlchemy ORM + SQLite (database)
- Jinja2 templates (dynamic HTML)
- HTML, CSS (frontend)
- Starlette signed-cookie sessions (login session)

## Windows setup
Open PowerShell in this folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:
- Website: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/api/health

## Demo credentials
| Role | Email | Password |
|---|---|---|
| Student | student@talenthub.demo | student |
| Company | company@talenthub.demo | company |
| Coordinator | coordinator@talenthub.demo | coordinator |
| Second student | priya@talenthub.demo | student |

## Features
- Student: academic profile, eligibility matching, apply, application tracking, offer response.
- Company: create job listings, inspect applicants, shortlist/reject, schedule interviews, issue offers.
- Coordinator: placement dashboard, branch-wise summary, offer register.
- JSON endpoints: `/api/jobs`, `/api/health`; interactive docs at `/docs`.

## Architecture
- Router/controller layer: FastAPI route handlers in `main.py`.
- Service/business rules: eligibility and workflow logic in route handlers (can be extracted into a dedicated `services/` package as the project grows).
- Data access/model layer: SQLAlchemy ORM models and database session.
- Database: SQLite file `talenthub.db`, created automatically.

## Important
This is an educational prototype. Before public deployment:
- Set a strong random `SessionMiddleware` secret via environment variable.
- Add CSRF protection for form posts, HTTPS, secure cookie settings, login rate limiting, password reset, audit logs and automated tests.
- Move service and repository logic into separate modules for a stricter layered architecture.
- Confirm institutional eligibility and placement policies before real use.
