from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

from db.database import init_db, get_all_jobs, update_status

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
async def dashboard(request: Request, status: str = "", search: str = ""):
    try:
        jobs = get_all_jobs(
            status=status if status else None,
            search=search if search else None
        )
    except Exception as e:
        print(f"Database error: {e}")
        jobs = []
    return templates.TemplateResponse("index.html", {
        "request": request,
        "jobs": jobs,
        "total": len(jobs),
        "status_filter": status,
        "search": search,
    })


@app.post("/update-status")
async def change_status(job_id: str = Form(...), status: str = Form(...)):
    update_status(job_id, status)
    return RedirectResponse("/", status_code=303)