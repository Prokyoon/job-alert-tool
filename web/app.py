from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List
import os

from db.database import init_db, get_all_jobs, update_status, bulk_update_status

init_db()

app = FastAPI()

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.head("/")
async def health_check():
    return Response(status_code=200)


@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    status: str = "",
    search: str = "",
    page: int = 1,
    per_page: int = 25
):
    try:
        all_jobs = get_all_jobs(
            status=status if status else None,
            search=search if search else None
        )
    except Exception as e:
        print(f"Database error: {e}")
        all_jobs = []

    total = len(all_jobs)
    per_page = per_page if per_page in [10, 25, 50, 100] else 25
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    jobs = all_jobs[start:start + per_page]

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


@app.post("/update-status")
async def change_status(job_id: str = Form(...), status: str = Form(...)):
    update_status(job_id, status)
    return RedirectResponse("/", status_code=303)


@app.post("/bulk-update-status")
async def bulk_update_status_route(
    job_ids: List[str] = Form(...),
    status: str = Form(...)
):
    bulk_update_status(job_ids, status)
    return RedirectResponse("/", status_code=303)