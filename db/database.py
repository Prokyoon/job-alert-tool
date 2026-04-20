import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id          TEXT PRIMARY KEY,
            company     TEXT NOT NULL,
            title       TEXT NOT NULL,
            location    TEXT,
            url         TEXT NOT NULL,
            ats_source  TEXT,
            date_found  TIMESTAMP NOT NULL DEFAULT NOW(),
            status      TEXT DEFAULT 'new',
            job_type    TEXT,
            experience  TEXT
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

def job_exists(job_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM jobs WHERE id = %s", (job_id,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def insert_job(job: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO jobs (id, company, title, location, url, ats_source, job_type, experience)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    ''', (
        job['id'], job['company'], job['title'],
        job.get('location', 'Remote'), job['url'],
        job.get('ats', 'unknown'),
        job.get('job_type'),
        job.get('experience'),
    ))
    conn.commit()
    cur.close()
    conn.close()

def get_all_jobs(status=None, search=None):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    if status:
        query += " AND status = %s"
        params.append(status)
    if search:
        query += " AND (title ILIKE %s OR company ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY date_found DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

def update_status(job_id: str, status: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE jobs SET status = %s WHERE id = %s", (status, job_id))
    conn.commit()
    cur.close()
    conn.close()

def bulk_update_status(job_ids: list, status: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany(
        "UPDATE jobs SET status = %s WHERE id = %s",
        [(status, job_id) for job_id in job_ids]
    )
    conn.commit()
    cur.close()
    conn.close()

def cleanup_old_jobs():
    conn = get_connection()
    cur = conn.cursor()
    cutoff = datetime.utcnow() - timedelta(days=30)
    cur.execute("DELETE FROM jobs WHERE date_found < %s", (cutoff,))
    conn.commit()
    cur.close()
    conn.close()
    print("Old jobs cleaned up.")