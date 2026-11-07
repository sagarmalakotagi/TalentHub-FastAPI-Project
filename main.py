from pathlib import Path
from datetime import datetime
import hashlib, hmac, secrets

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine, String, Integer, Float, ForeignKey, DateTime, Text, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'talenthub.db'}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

app = FastAPI(title="TalentHub API", description="Campus Placement Management System")
app.add_middleware(SessionMiddleware, secret_key="replace-this-with-a-long-random-secret")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20))
    student: Mapped["Student"] = relationship(back_populates="user", uselist=False)
    company: Mapped["Company"] = relationship(back_populates="user", uselist=False)


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    branch: Mapped[str] = mapped_column(String(100))
    cgpa: Mapped[float] = mapped_column(Float)
    backlogs: Mapped[int] = mapped_column(Integer, default=0)
    user: Mapped[User] = relationship(back_populates="student")
    applications: Mapped[list["Application"]] = relationship(back_populates="student")


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    company_name: Mapped[str] = mapped_column(String(140))
    user: Mapped[User] = relationship(back_populates="company")
    jobs: Mapped[list["Job"]] = relationship(back_populates="company")


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    title: Mapped[str] = mapped_column(String(140))
    description: Mapped[str] = mapped_column(Text, default="")
    branch: Mapped[str] = mapped_column(String(100), default="Any")
    min_cgpa: Mapped[float] = mapped_column(Float)
    max_backlogs: Mapped[int] = mapped_column(Integer)
    location: Mapped[str] = mapped_column(String(120), default="Not specified")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    company: Mapped[Company] = relationship(back_populates="jobs")
    applications: Mapped[list["Application"]] = relationship(back_populates="job")


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    status: Mapped[str] = mapped_column(String(40), default="Applied")
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    job: Mapped[Job] = relationship(back_populates="applications")
    student: Mapped[Student] = relationship(back_populates="applications")
    interview: Mapped["Interview"] = relationship(back_populates="application", uselist=False)
    offer: Mapped["Offer"] = relationship(back_populates="application", uselist=False)


class Interview(Base):
    __tablename__ = "interviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), unique=True)
    interview_at: Mapped[datetime] = mapped_column(DateTime)
    mode: Mapped[str] = mapped_column(String(30), default="Online")
    notes: Mapped[str] = mapped_column(Text, default="")
    application: Mapped[Application] = relationship(back_populates="interview")


class Offer(Base):
    __tablename__ = "offers"
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), unique=True)
    package: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(30), default="Issued")
    application: Mapped[Application] = relationship(back_populates="offer")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 180_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 180_000).hex()
        return hmac.compare_digest(candidate, digest)
    except ValueError:
        return False


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user(request: Request, db: Session) -> User | None:
    uid = request.session.get("user_id")
    return db.get(User, uid) if uid else None


def require_role(request: Request, db: Session, *roles) -> User:
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Please sign in")
    if user.role not in roles:
        raise HTTPException(status_code=403, detail="You do not have permission")
    return user


def page(request: Request, template: str, user: User | None = None, **context):
    return templates.TemplateResponse(template, {
        "request": request, "current_user": user.name if user else None,
        "current_role": user.role if user else None, **context
    })


def init_db():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(func.count(User.id))) == 0:
            student_user = User(name="Rahul Student", email="student@talenthub.demo",
                                password_hash=hash_password("student"), role="student")
            company_user = User(name="ABC Technologies", email="company@talenthub.demo",
                                password_hash=hash_password("company"), role="company")
            coordinator = User(name="Placement Coordinator", email="coordinator@talenthub.demo",
                               password_hash=hash_password("coordinator"), role="coordinator")
            second_user = User(name="Priya Student", email="priya@talenthub.demo",
                               password_hash=hash_password("student"), role="student")
            db.add_all([student_user, company_user, coordinator, second_user])
            db.flush()
            student = Student(user_id=student_user.id, branch="Computer Science", cgpa=8.2, backlogs=1)
            second = Student(user_id=second_user.id, branch="Information Science", cgpa=7.6, backlogs=0)
            company = Company(user_id=company_user.id, company_name="ABC Technologies")
            db.add_all([student, second, company])
            db.flush()
            db.add(Job(company_id=company.id, title="Software Developer",
                       description="Build and maintain software applications.",
                       branch="Any", min_cgpa=7.0, max_backlogs=2, location="Bengaluru"))
            db.commit()


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if user:
        return RedirectResponse("/dashboard", status_code=303)
    return page(request, "home.html")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return page(request, "login.html")


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...),
          db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))
    if not user or not verify_password(password, user.password_hash):
        return page(request, "login.html", error="Invalid email or password.")
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    if user.role == "student":
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        jobs = db.scalars(select(Job).order_by(Job.id.desc())).all()
        job_rows = []
        for job in jobs:
            applied = db.scalar(select(Application).where(
                Application.job_id == job.id, Application.student_id == student.id))
            eligible = (student.cgpa >= job.min_cgpa and student.backlogs <= job.max_backlogs
                        and (job.branch == "Any" or job.branch.lower() == student.branch.lower()))
            job_rows.append({"job": job, "company": job.company.company_name,
                             "eligible": eligible, "applied": bool(applied)})
        applications = db.scalars(select(Application).where(
            Application.student_id == student.id).order_by(Application.id.desc())).all()
        offers = [a.offer for a in applications if a.offer]
        return page(request, "student_dashboard.html", user, student=student,
                    jobs=job_rows, applications=applications, offers=offers)

    if user.role == "company":
        company = db.scalar(select(Company).where(Company.user_id == user.id))
        jobs = db.scalars(select(Job).where(Job.company_id == company.id).order_by(Job.id.desc())).all()
        applications = db.scalars(select(Application).join(Job).where(
            Job.company_id == company.id).order_by(Application.id.desc())).all()
        return page(request, "company_dashboard.html", user, company=company,
                    jobs=jobs, applications=applications)

    stats = {
        "students": db.scalar(select(func.count(Student.id))) or 0,
        "companies": db.scalar(select(func.count(Company.id))) or 0,
        "jobs": db.scalar(select(func.count(Job.id))) or 0,
        "applications": db.scalar(select(func.count(Application.id))) or 0,
        "placed": db.scalar(select(func.count(Offer.id)).where(Offer.status == "Accepted")) or 0
    }
    recent = db.scalars(select(Application).order_by(Application.id.desc()).limit(8)).all()
    return page(request, "coordinator_dashboard.html", user, stats=stats, recent=recent)


@app.post("/jobs/{job_id}/apply")
def apply_job(job_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_role(request, db, "student")
    student = db.scalar(select(Student).where(Student.user_id == user.id))
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    eligible = (student.cgpa >= job.min_cgpa and student.backlogs <= job.max_backlogs
                and (job.branch == "Any" or job.branch.lower() == student.branch.lower()))
    existing = db.scalar(select(Application).where(
        Application.job_id == job_id, Application.student_id == student.id))
    if eligible and not existing:
        db.add(Application(job_id=job_id, student_id=student.id))
        db.commit()
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/jobs/create")
def create_job(request: Request, title: str = Form(...), description: str = Form(""),
               branch: str = Form("Any"), location: str = Form(""),
               min_cgpa: float = Form(...), max_backlogs: int = Form(...),
               db: Session = Depends(get_db)):
    user = require_role(request, db, "company")
    if not 0 <= min_cgpa <= 10 or max_backlogs < 0:
        raise HTTPException(400, "Invalid eligibility criteria")
    company = db.scalar(select(Company).where(Company.user_id == user.id))
    db.add(Job(company_id=company.id, title=title.strip(), description=description,
               branch=branch.strip() or "Any", location=location,
               min_cgpa=min_cgpa, max_backlogs=max_backlogs))
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/applications/{application_id}/status")
def update_status(application_id: int, request: Request, status: str = Form(...),
                  db: Session = Depends(get_db)):
    user = require_role(request, db, "company")
    allowed = {"Shortlisted", "Rejected", "Interview Scheduled", "Selected"}
    app_row = db.get(Application, application_id)
    if not app_row or app_row.job.company.user_id != user.id:
        raise HTTPException(404, "Application not found")
    if status in allowed:
        app_row.status = status
        db.commit()
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/applications/{application_id}/interview")
def schedule_interview(application_id: int, request: Request,
                       interview_at: str = Form(...), mode: str = Form("Online"),
                       db: Session = Depends(get_db)):
    user = require_role(request, db, "company")
    app_row = db.get(Application, application_id)
    if not app_row or app_row.job.company.user_id != user.id:
        raise HTTPException(404, "Application not found")
    when = datetime.fromisoformat(interview_at)
    interview = app_row.interview
    if interview:
        interview.interview_at, interview.mode = when, mode
    else:
        db.add(Interview(application_id=application_id, interview_at=when, mode=mode))
    app_row.status = "Interview Scheduled"
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/applications/{application_id}/offer")
def issue_offer(application_id: int, request: Request, package: float = Form(...),
                db: Session = Depends(get_db)):
    user = require_role(request, db, "company")
    app_row = db.get(Application, application_id)
    if not app_row or app_row.job.company.user_id != user.id:
        raise HTTPException(404, "Application not found")
    if package < 0:
        raise HTTPException(400, "Package cannot be negative")
    if app_row.offer:
        app_row.offer.package, app_row.offer.status = package, "Issued"
    else:
        db.add(Offer(application_id=application_id, package=package, status="Issued"))
    app_row.status = "Selected"
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/offers/{offer_id}/respond")
def respond_offer(offer_id: int, request: Request, decision: str = Form(...),
                  db: Session = Depends(get_db)):
    user = require_role(request, db, "student")
    offer = db.get(Offer, offer_id)
    if not offer or offer.application.student.user_id != user.id:
        raise HTTPException(404, "Offer not found")
    if decision in {"Accepted", "Declined"}:
        offer.status = decision
        db.commit()
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    user = require_role(request, db, "student")
    student = db.scalar(select(Student).where(Student.user_id == user.id))
    return page(request, "profile.html", user, student=student)


@app.post("/profile")
def update_profile(request: Request, branch: str = Form(...), cgpa: float = Form(...),
                   backlogs: int = Form(...), db: Session = Depends(get_db)):
    user = require_role(request, db, "student")
    student = db.scalar(select(Student).where(Student.user_id == user.id))
    if not 0 <= cgpa <= 10 or backlogs < 0:
        raise HTTPException(400, "Invalid profile values")
    student.branch, student.cgpa, student.backlogs = branch.strip(), cgpa, backlogs
    db.commit()
    return RedirectResponse("/profile", status_code=303)


@app.get("/reports", response_class=HTMLResponse)
def reports(request: Request, db: Session = Depends(get_db)):
    user = require_role(request, db, "coordinator")
    students = db.scalars(select(Student)).all()
    branch_rows = []
    for branch in sorted({s.branch for s in students}):
        group = [s for s in students if s.branch == branch]
        placed = sum(1 for s in group if any(
            a.offer and a.offer.status == "Accepted" for a in s.applications))
        branch_rows.append({"branch": branch, "students": len(group), "placed": placed})
    offers = db.scalars(select(Offer).order_by(Offer.id.desc())).all()
    return page(request, "reports.html", user, branches=branch_rows, offers=offers)


# Small JSON API endpoints for testing with Swagger UI (/docs)
@app.get("/api/jobs")
def api_jobs(db: Session = Depends(get_db)):
    jobs = db.scalars(select(Job).order_by(Job.id.desc())).all()
    return [{"id": j.id, "title": j.title, "company": j.company.company_name,
             "min_cgpa": j.min_cgpa, "max_backlogs": j.max_backlogs,
             "branch": j.branch, "location": j.location} for j in jobs]


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "TalentHub FastAPI"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
