from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sys, os
from db.database import init_db

init_db()
 
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.database import get_all_jobs, update_status
 
app = FastAPI()
templates = Jinja2Templates(directory='web/templates')
app.mount('/static', StaticFiles(directory='web/static'), name='static')
 
@app.get('/', response_class=HTMLResponse)
async def dashboard(request: Request, status: str = '', search: str = ''):
    jobs = get_all_jobs(
        status=status if status else None,
        search=search if search else None
    )
    return templates.TemplateResponse('index.html', {
        'request': request,
        'jobs': jobs,
        'total': len(jobs),
        'status_filter': status,
        'search': search,
    })
 
@app.post('/update-status')
async def change_status(job_id: str = Form(...), status: str = Form(...)):
    update_status(job_id, status)
    return RedirectResponse('/', status_code=303)