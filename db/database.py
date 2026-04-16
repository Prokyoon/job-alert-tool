import sqlite3
import hashlib
from datetime import datetime, timedelta
import os
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "jobs.db")
 
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
 
def init_db():
    conn = get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id          TEXT PRIMARY KEY,
            company     TEXT NOT NULL,
            title       TEXT NOT NULL,
            location    TEXT,
            url         TEXT NOT NULL,
            ats_source  TEXT,
            date_found  TEXT NOT NULL,
            status      TEXT DEFAULT 'new'
        )
    ''')
    conn.commit()
    conn.close()
 
def job_exists(job_id: str) -> bool:
    conn = get_connection()
    row = conn.execute('SELECT 1 FROM jobs WHERE id = ?', (job_id,)).fetchone()
    conn.close()
    return row is not None
 
def insert_job(job: dict):
    conn = get_connection()
    conn.execute('''
        INSERT OR IGNORE INTO jobs
        (id, company, title, location, url, ats_source, date_found)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        job['id'], job['company'], job['title'],
        job.get('location', 'Remote'), job['url'],
        job.get('ats'), datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
 
def get_all_jobs(status=None, search=None):
    conn = get_connection()
    query = 'SELECT * FROM jobs WHERE 1=1'
    params = []
    if status:
        query += ' AND status = ?'
        params.append(status)
    if search:
        query += ' AND (title LIKE ? OR company LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    query += ' ORDER BY date_found DESC'
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]
 
def update_status(job_id: str, status: str):
    conn = get_connection()
    conn.execute('UPDATE jobs SET status = ? WHERE id = ?', (status, job_id))
    conn.commit()
    conn.close()
 
def cleanup_old_jobs():
    conn = get_connection()
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    conn.execute('DELETE FROM jobs WHERE date_found < ?', (cutoff,))
    conn.commit()
    conn.close()
    print('Old jobs cleaned up.')