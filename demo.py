#!/usr/bin/env python3
"""
demo.py — Seed or clear fake demo jobs in the database.

Usage (from project root):
    python demo.py seed    # insert 15 realistic demo jobs tagged demo=true
    python demo.py clear   # delete all demo jobs

The demo jobs use IDs prefixed with "demo-" so they never collide with real jobs.
"""
import sys
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import random

load_dotenv()

DEMO_JOBS = [
    {
        "id": "demo-001",
        "company": "Stripe",
        "title": "Technical Support Engineer",
        "location": "Remote, Europe",
        "url": "https://stripe.com/jobs/demo-001",
        "ats_source": "greenhouse",
        "job_type": "Full-time",
        "experience": "Mid-level",
        "status": "new",
    },
    {
        "id": "demo-002",
        "company": "Wise",
        "title": "Customer Support Specialist",
        "location": "London, UK",
        "url": "https://wise.com/jobs/demo-002",
        "ats_source": "lever",
        "job_type": "Full-time",
        "experience": "Junior",
        "status": "new",
    },
    {
        "id": "demo-003",
        "company": "Revolut",
        "title": "Technical Account Manager",
        "location": "Bucharest, Romania",
        "url": "https://revolut.com/jobs/demo-003",
        "ats_source": "workable",
        "job_type": "Full-time",
        "experience": "Senior",
        "status": "new",
    },
    {
        "id": "demo-004",
        "company": "Adyen",
        "title": "Implementation Specialist",
        "location": "Amsterdam, Netherlands",
        "url": "https://adyen.com/jobs/demo-004",
        "ats_source": "ashby",
        "job_type": "Full-time",
        "experience": "Mid-level",
        "status": "new",
    },
    {
        "id": "demo-005",
        "company": "Klarna",
        "title": "Customer Success Manager",
        "location": "Stockholm, Sweden",
        "url": "https://klarna.com/jobs/demo-005",
        "ats_source": "greenhouse",
        "job_type": "Full-time",
        "experience": "Senior",
        "status": "new",
    },
    {
        "id": "demo-006",
        "company": "Monzo",
        "title": "Support Specialist",
        "location": "Remote, UK",
        "url": "https://monzo.com/jobs/demo-006",
        "ats_source": "lever",
        "job_type": "Full-time",
        "experience": "Junior",
        "status": "new",
    },
    {
        "id": "demo-007",
        "company": "Checkout.com",
        "title": "Solutions Engineer",
        "location": "Remote, EMEA",
        "url": "https://checkout.com/jobs/demo-007",
        "ats_source": "greenhouse",
        "job_type": "Full-time",
        "experience": "Senior",
        "status": "new",
    },
    {
        "id": "demo-008",
        "company": "Mambu",
        "title": "Implementation Consultant",
        "location": "Berlin, Germany",
        "url": "https://mambu.com/jobs/demo-008",
        "ats_source": "workable",
        "job_type": "Full-time",
        "experience": "Mid-level",
        "status": "new",
    },
    {
        "id": "demo-009",
        "company": "Temenos",
        "title": "Technical Support Analyst",
        "location": "Geneva, Switzerland",
        "url": "https://temenos.com/jobs/demo-009",
        "ats_source": "smartrecruiters",
        "job_type": "Full-time",
        "experience": "Mid-level",
        "status": "new",
    },
    {
        "id": "demo-010",
        "company": "Finastra",
        "title": "Onboarding Specialist",
        "location": "Remote, Europe",
        "url": "https://finastra.com/jobs/demo-010",
        "ats_source": "greenhouse",
        "job_type": "Full-time",
        "experience": "Junior",
        "status": "new",
    },
    {
        "id": "demo-011",
        "company": "SumUp",
        "title": "Customer Support Engineer",
        "location": "Cologne, Germany",
        "url": "https://sumup.com/jobs/demo-011",
        "ats_source": "lever",
        "job_type": "Full-time",
        "experience": "Mid-level",
        "status": "new",
    },
    {
        "id": "demo-012",
        "company": "Paysafe",
        "title": "Technical Support Lead",
        "location": "Sofia, Bulgaria",
        "url": "https://paysafe.com/jobs/demo-012",
        "ats_source": "ashby",
        "job_type": "Full-time",
        "experience": "Senior",
        "status": "new",
    },
    {
        "id": "demo-013",
        "company": "Backbase",
        "title": "Implementation Manager",
        "location": "Amsterdam, Netherlands",
        "url": "https://backbase.com/jobs/demo-013",
        "ats_source": "teamtailor",
        "job_type": "Full-time",
        "experience": "Manager",
        "status": "new",
    },
    {
        "id": "demo-014",
        "company": "Plaid",
        "title": "Customer Onboarding Specialist",
        "location": "Remote, Europe",
        "url": "https://plaid.com/jobs/demo-014",
        "ats_source": "greenhouse",
        "job_type": "Full-time",
        "experience": "Junior",
        "status": "new",
    },
    {
        "id": "demo-015",
        "company": "Nuvei",
        "title": "Implementation Engineer",
        "location": "Dublin, Ireland",
        "url": "https://nuvei.com/jobs/demo-015",
        "ats_source": "workable",
        "job_type": "Contract",
        "experience": "Mid-level",
        "status": "new",
    },
]

# Spread out date_found over the last 7 days so the list looks natural
_now = datetime.now(timezone.utc)
for i, job in enumerate(DEMO_JOBS):
    offset_hours = random.randint(0, 7 * 24)
    job["date_found"] = _now - timedelta(hours=offset_hours)


def get_conn():
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL not set. Check your .env file.")
    return psycopg2.connect(url)


def seed():
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    for job in DEMO_JOBS:
        cur.execute(
            """
            INSERT INTO jobs (id, company, title, location, url, ats_source,
                              job_type, experience, status, date_found)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                job["id"], job["company"], job["title"], job["location"],
                job["url"], job["ats_source"], job["job_type"],
                job["experience"], job["status"], job["date_found"],
            ),
        )
        if cur.rowcount:
            inserted += 1
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅  Seeded {inserted} demo jobs ({len(DEMO_JOBS) - inserted} already existed).")


def clear():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM jobs WHERE id LIKE 'demo-%'")
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    print(f"🗑️   Deleted {deleted} demo jobs.")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("seed", "clear"):
        print("Usage: python demo.py seed | clear")
        sys.exit(1)

    if sys.argv[1] == "seed":
        seed()
    else:
        clear()
