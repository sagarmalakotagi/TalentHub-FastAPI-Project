# TalentHub | Campus Placement Management System

A FastAPI-based campus placement management system.

---

## 1. Technology Stack

The project uses the following technologies:

| Technology | Purpose |
|---|---|
| FastAPI + Uvicorn | Backend |
| SQLAlchemy ORM + SQLite | Database |
| Jinja2 Templates | Dynamic HTML |
| HTML, CSS | Frontend |
| Starlette Signed-Cookie Sessions | Login Session |

## 2. Installation and Setup (Windows)

Open PowerShell in the project folder and execute the following commands in order.

**Step 1: Create a virtual environment**

```powershell
python -m venv .venv
```

**Step 2: Activate the virtual environment**

```powershell
.venv\Scripts\Activate.ps1
```

**Step 3: Install project dependencies**

```powershell
pip install -r requirements.txt
```

**Step 4: Start the application**

```powershell
uvicorn main:app --reload
```

### Application Access

After starting the server, access the application using these URLs:

| Service | URL |
|---|---|
| Website | http://127.0.0.1:8000 |
| Interactive API Documentation | http://127.0.0.1:8000/docs |
| Health Endpoint | http://127.0.0.1:8000/api/health |

## 3. Demo Login Credentials

The following credentials are available for testing different user roles.

| Role | Email | Password |
|---|---|---|
| Student | student@talenthub.demo | student |
| Company | company@talenthub.demo | company |
| Coordinator | coordinator@talenthub.demo | coordinator |
| Second Student | priya@talenthub.demo | student |

## 4. System Features

### Student Module
- Academic profile management.
- Eligibility matching.
- Job application.
- Application tracking.
- Offer response.

### Company Module
- Create job listings.
- Inspect applicants.
- Shortlist or reject applicants.
- Schedule interviews.
- Issue offers.

### Coordinator Module
- Placement dashboard.
- Branch-wise summary.
- Offer register.

### API Endpoints
- JSON endpoint: `/api/jobs`
- Health endpoint: `/api/health`
- Interactive API documentation: `/docs`

## 5. System Architecture

The application follows the following architectural structure:

**Router / Controller Layer**
- FastAPI route handlers are implemented in `main.py`.

**Service / Business Logic Layer**
- Eligibility and workflow logic are implemented in route handlers.
- This logic can be extracted into a dedicated `services/` package as the project grows.

**Data Access / Model Layer**
- SQLAlchemy ORM models.
- Database session.

**Database Layer**
- SQLite database.
- Database file: `talenthub.db`.
- Created automatically.

## 6. Important Considerations

This project is an educational prototype. The following improvements should be implemented before public deployment:

- Set a strong random `SessionMiddleware` secret using an environment variable.
- Add CSRF protection for form posts.
- Enable HTTPS and secure cookie settings.
- Implement login rate limiting.
- Add password reset functionality.
- Maintain audit logs.
- Implement automated tests.
- Move service and repository logic into separate modules for a stricter layered architecture.
- Confirm institutional eligibility and placement policies before real use.
