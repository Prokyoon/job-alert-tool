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

    # --- existing jobs table ---
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

    # --- NEW: audit log table ---
    cur.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id          SERIAL PRIMARY KEY,
            job_id      TEXT NOT NULL,
            new_status  TEXT NOT NULL,
            changed_at  TIMESTAMP DEFAULT NOW(),
            ip          TEXT
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

def get_all_jobs(status=None, search=None, limit=100, offset=0):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    base = "FROM jobs WHERE 1=1"
    params = []
    if status:
        base += " AND status = %s"
        params.append(status)
    if search:
        base += " AND (title ILIKE %s OR company ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    # Total count (same filters, no pagination)
    cur.execute(f"SELECT COUNT(*) {base}", params)
    total = cur.fetchone()[0]

    # Paginated rows
    cur.execute(
        f"SELECT * {base} ORDER BY date_found DESC LIMIT %s OFFSET %s",
        params + [limit, offset],
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows], total

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

# ── NEW: audit log functions ──────────────────────────────────────────────────

def log_audit(job_id: str, new_status: str, ip: str = ""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO audit_log (job_id, new_status, ip) VALUES (%s, %s, %s)",
        (job_id, new_status, ip),
    )
    conn.commit()
    cur.close()
    conn.close()

def get_stats():
    """Return pipeline metrics for the /stats dashboard page."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Status breakdown
    cur.execute("""
        SELECT status, COUNT(*) AS count
        FROM jobs
        GROUP BY status
        ORDER BY count DESC
    """)
    status_counts = {r["status"]: r["count"] for r in cur.fetchall()}

    # ATS source breakdown
    cur.execute("""
        SELECT ats_source, COUNT(*) AS count
        FROM jobs
        GROUP BY ats_source
        ORDER BY count DESC
        LIMIT 10
    """)
    ats_counts = [dict(r) for r in cur.fetchall()]

    # Jobs found per day (last 14 days)
    cur.execute("""
        SELECT DATE(date_found) AS day, COUNT(*) AS count
        FROM jobs
        WHERE date_found >= NOW() - INTERVAL '14 days'
        GROUP BY day
        ORDER BY day ASC
    """)
    daily_counts = [dict(r) for r in cur.fetchall()]

    # Recent audit activity (last 7 days), grouped by day + action
    cur.execute("""
        SELECT DATE(changed_at) AS day, new_status, COUNT(*) AS count
        FROM audit_log
        WHERE changed_at >= NOW() - INTERVAL '7 days'
        GROUP BY day, new_status
        ORDER BY day ASC
    """)
    audit_activity = [dict(r) for r in cur.fetchall()]

    # Total companies monitored (distinct companies in jobs table)
    cur.execute("SELECT COUNT(DISTINCT company) FROM jobs")
    total_companies = cur.fetchone()[0]

    # Total ATS platforms
    cur.execute("SELECT COUNT(DISTINCT ats_source) FROM jobs")
    total_ats = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "status_counts":   status_counts,
        "ats_counts":      ats_counts,
        "daily_counts":    daily_counts,
        "audit_activity":  audit_activity,
        "total_companies": total_companies,
        "total_ats":       total_ats,
        "total_jobs":      sum(status_counts.values()),
    }


def get_export_jobs(status=None):
    """Return all jobs as plain dicts for CSV export."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = "SELECT id, company, title, location, url, ats_source, job_type, experience, status, date_found FROM jobs WHERE 1=1"
    params = []
    if status:
        query += " AND status = %s"
        params.append(status)
    query += " ORDER BY date_found DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def health_check_db() -> dict:
    """Verify DB connectivity and return basic counts. Used by /health endpoint."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM jobs")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM jobs WHERE status = 'new'")
        new_jobs = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"status": "ok", "total_jobs": total, "new_jobs": new_jobs}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def get_audit_log(limit: int = 200):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            a.id,
            a.job_id,
            COALESCE(j.title,   'Unknown') AS title,
            COALESCE(j.company, 'Unknown') AS company,
            a.new_status,
            a.changed_at,
            a.ip
        FROM audit_log a
        LEFT JOIN jobs j ON j.id = a.job_id
        ORDER BY a.changed_at DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]