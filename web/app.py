from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from typing import List
import os
import secrets
from datetime import datetime, timezone

from db.database import init_db, get_all_jobs, update_status, bulk_update_status

init_db()

app = FastAPI()

# ── Session middleware ────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
SESSION_LIFETIME = 10 * 60  # 10 minutes in seconds

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="jobradar_session",
    max_age=SESSION_LIFETIME,
    same_site="lax",
    https_only=False,
)

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ── Users ─────────────────────────────────────────────────────────────────────
USERS = {
    os.getenv("ADMIN_USER", "admin"): {
        "password": os.getenv("ADMIN_PASS", "admin"),
        "role": "admin",
    },
    os.getenv("DEMO_USER", "demo"): {
        "password": os.getenv("DEMO_PASS", "demo"),
        "role": "demo",
    },
}

# ── Auth helpers ──────────────────────────────────────────────────────────────

def _session_valid(request: Request) -> bool:
    user = request.session.get("user")
    ts   = request.session.get("ts")
    if not user or ts is None:
        return False
    age = datetime.now(timezone.utc).timestamp() - ts
    return age < SESSION_LIFETIME


def get_current_user(request: Request):
    if _session_valid(request):
        return {
            "username": request.session.get("user"),
            "role":     request.session.get("role", "user"),
        }
    return None


# ── Touch session timestamp on every authenticated request ────────────────────

@app.middleware("http")
async def refresh_session_timestamp(request: Request, call_next):
    response = await call_next(request)
    if _session_valid(request):
        request.session["ts"] = datetime.now(timezone.utc).timestamp()
    return response


# ── Health check ──────────────────────────────────────────────────────────────

@app.head("/")
async def health_check():
    return Response(status_code=200)


# ── Login / Logout ────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    user = USERS.get(username)
    if user and user["password"] == password:
        request.session["user"] = username
        request.session["role"] = user["role"]
        request.session["ts"]   = datetime.now(timezone.utc).timestamp()
        return RedirectResponse("/?status=new&per_page=100", status_code=303)
    return RedirectResponse("/login?error=Invalid+username+or+password", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    status: str = "new",
    search: str = "",
    page: int = 1,
    per_page: int = 100,
):
    if not _session_valid(request):
        return RedirectResponse("/login", status_code=303)

    current_user = get_current_user(request)

    try:
        all_jobs = get_all_jobs(
            status=status if status else None,
            search=search if search else None,
        )
    except Exception as e:
        print(f"Database error: {e}")
        all_jobs = []

    total       = len(all_jobs)
    per_page    = per_page if per_page in [10, 25, 50, 100] else 100
    total_pages = max(1, (total + per_page - 1) // per_page)
    page        = max(1, min(page, total_pages))
    start       = (page - 1) * per_page
    jobs        = all_jobs[start : start + per_page]

    return templates.TemplateResponse("index.html", {
        "request":       request,
        "jobs":          jobs,
        "total":         total,
        "status_filter": status,
        "search":        search,
        "page":          page,
        "per_page":      per_page,
        "total_pages":   total_pages,
        "current_user":  current_user,
    })


# ── Status updates ────────────────────────────────────────────────────────────

@app.get("/update-status")
async def update_status_get(request: Request):
    if not _session_valid(request):
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/?status=new&per_page=100", status_code=303)


@app.get("/bulk-update-status")
async def bulk_update_status_get(request: Request):
    if not _session_valid(request):
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/?status=new&per_page=100", status_code=303)


@app.post("/update-status")
async def change_status(
    request: Request,
    job_id: str = Form(...),
    status: str = Form(...),
    current_status: str = Form("new"),
    current_search: str = Form(""),
    current_page: int = Form(1),
    current_per_page: int = Form(100),
):
    if not _session_valid(request):
        return RedirectResponse("/login", status_code=303)
    update_status(job_id, status)
    return RedirectResponse(
        f"/?status={current_status}&search={current_search}"
        f"&page={current_page}&per_page={current_per_page}",
        status_code=303,
    )


@app.post("/bulk-update-status")
async def bulk_update_status_route(
    request: Request,
    job_ids: List[str] = Form(...),
    status: str = Form(...),
    current_status: str = Form("new"),
    current_search: str = Form(""),
    current_page: int = Form(1),
    current_per_page: int = Form(100),
):
    if not _session_valid(request):
        return RedirectResponse("/login", status_code=303)
    bulk_update_status(job_ids, status)
    return RedirectResponse(
        f"/?status={current_status}&search={current_search}"
        f"&page={current_page}&per_page={current_per_page}",
        status_code=303,
    )
