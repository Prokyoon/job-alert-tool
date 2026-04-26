from fastapi import FastAPI, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List
import os

from db.database import init_db, get_all_jobs, update_status, bulk_update_status, log_audit

init_db()

app = FastAPI()

# ── Rate limiting ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ── Auth config ───────────────────────────────────────────────────────────────
SECRET_KEY   = os.getenv("SECRET_KEY", "change-me-in-production")
DASHBOARD_USER = os.getenv("DASHBOARD_USER", "admin")
DASHBOARD_PASS = os.getenv("DASHBOARD_PASS", "changeme")
COOKIE_NAME  = "jobradar_session"
COOKIE_MAX_AGE = 60 * 60 * 8   # 8 hours

serializer = URLSafeTimedSerializer(SECRET_KEY)


def _make_session_cookie(username: str) -> str:
    return serializer.dumps({"u": username})


def _get_current_user(request: Request):
    """Return username if session cookie is valid, else None."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=COOKIE_MAX_AGE)
        return data.get("u")
    except (BadSignature, SignatureExpired):
        return None


def require_login(request: Request):
    """Dependency — redirects to /login if not authenticated."""
    user = _get_current_user(request)
    if not user:
        # Store the original destination so we can redirect after login
        dest = str(request.url)
        raise _redirect_to_login(dest)
    return user


def _redirect_to_login(next_url: str = "/"):
    from fastapi import HTTPException
    # We raise a redirect as an exception so it works inside Depends()
    response = RedirectResponse(f"/login?next={next_url}", status_code=303)
    raise _LoginRedirect(response)


class _LoginRedirect(Exception):
    def __init__(self, response):
        self.response = response


from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    """Intercept _LoginRedirect exceptions and return the redirect response."""
    OPEN_PATHS = {"/login", "/health"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.OPEN_PATHS or request.method == "HEAD":
            return await call_next(request)
        user = _get_current_user(request)
        if not user:
            next_url = str(request.url)
            return RedirectResponse(f"/login?next={next_url}", status_code=303)
        return await call_next(request)

app.add_middleware(AuthMiddleware)


# ── Security headers ──────────────────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"]        = "DENY"
        response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]     = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' cdn.tailwindcss.com 'unsafe-inline'; "
            "img-src 'self' img.logo.dev data:; "
            "style-src 'self' cdn.tailwindcss.com fonts.googleapis.com 'unsafe-inline'; "
            "font-src fonts.gstatic.com; "
            "connect-src 'none'"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)


# ── Health check (unauthenticated — needed by Render) ────────────────────────
@app.head("/")
@app.get("/health")
async def health_check():
    return Response(status_code=200)


# ── Login ─────────────────────────────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/", error: str = ""):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "next": next,
        "error": error,
    })


@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
):
    if username == DASHBOARD_USER and password == DASHBOARD_PASS:
        token = _make_session_cookie(username)
        # Safety: only redirect to relative paths
        safe_next = next if next.startswith("/") else "/"
        response = RedirectResponse(safe_next, status_code=303)
        response.set_cookie(
            COOKIE_NAME,
            token,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=True,   # set False only for local HTTP testing
        )
        return response
    return RedirectResponse("/login?error=1", status_code=303)


@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response


# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    status: str = "",
    search: str = Query(default="", max_length=100),  # Step 6: cap search length
    page: int = 1,
    per_page: int = 100,
):
    per_page = per_page if per_page in [10, 25, 50, 100] else 100
    offset   = (page - 1) * per_page

    try:
        jobs, total = get_all_jobs(          # Step 5: SQL pagination
            status=status if status else None,
            search=search if search else None,
            limit=per_page,
            offset=offset,
        )
    except Exception as e:
        print(f"Database error: {e}")
        jobs, total = [], 0

    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    return templates.TemplateResponse("index.html", {
        "request": request,
        "jobs": jobs,
        "total": total,
        "status_filter": status,
        "search": search,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    })


@app.get("/update-status")
async def update_status_get():
    return RedirectResponse("/?status=new&per_page=100", status_code=303)


@app.get("/bulk-update-status")
async def bulk_update_status_get():
    return RedirectResponse("/?status=new&per_page=100", status_code=303)


@app.post("/update-status")
@limiter.limit("500/minute")
async def change_status(
    request: Request,
    job_id: str = Form(...),
    status: str = Form(...),
    current_status: str = Form("new"),
    current_search: str = Form(""),
    current_page: int = Form(1),
    current_per_page: int = Form(100),
):
    update_status(job_id, status)
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
    log_audit(job_id, status, ip)
    return RedirectResponse(
        f"/?status={current_status}&search={current_search}"
        f"&page={current_page}&per_page={current_per_page}",
        status_code=303,
    )


@app.post("/bulk-update-status")
@limiter.limit("500/minute")
async def bulk_update_status_route(
    request: Request,
    job_ids: List[str] = Form(...),
    status: str = Form(...),
    current_status: str = Form("new"),
    current_search: str = Form(""),
    current_page: int = Form(1),
    current_per_page: int = Form(100),
):
    if len(job_ids) > 200:
        return RedirectResponse("/?error=too_many", status_code=303)
    bulk_update_status(job_ids, status)
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
    for job_id in job_ids:
        log_audit(job_id, status, ip)
    return RedirectResponse(
        f"/?status={current_status}&search={current_search}"
        f"&page={current_page}&per_page={current_per_page}",
        status_code=303,
    )