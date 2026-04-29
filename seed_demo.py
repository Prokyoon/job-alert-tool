"""
seed_demo.py — populate the database with realistic demo jobs.

Usage:
    python seed_demo.py          # insert demo jobs (skips existing)
    python seed_demo.py --reset  # wipe demo jobs first, then re-insert

Place this file in the repo root and run it once before sharing the demo URL.
"""

import os
import sys
import argparse
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Demo jobs ─────────────────────────────────────────────────────────────────
# Realistic roles across RegTech, FinTech, and enterprise SaaS —
# exactly the companies Job Radar is built to monitor.
# Statuses are varied so the pipeline looks lived-in, not empty.

DEMO_JOBS = [
    {
        "id":         "demo_001",
        "company":    "Stripe",
        "title":      "Technical Account Manager, EMEA",
        "location":   "Remote, Europe",
        "url":        "https://stripe.com/jobs/listing/technical-account-manager-emea",
        "ats":        "greenhouse",
        "job_type":   "Full-time",
        "experience": "Senior",
        "status":     "new",
        "days_ago":   0,
    },
    {
        "id":         "demo_002",
        "company":    "Revolut",
        "title":      "Customer Support Team Lead",
        "location":   "Kraków, Poland",
        "url":        "https://www.revolut.com/careers/position/customer-support-team-lead",
        "ats":        "lever",
        "job_type":   "Full-time",
        "experience": "Manager",
        "status":     "new",
        "days_ago":   1,
    },
    {
        "id":         "demo_003",
        "company":    "Wise",
        "title":      "Technical Support Engineer",
        "location":   "Tallinn, Estonia",
        "url":        "https://wise.com/gb/careers/technical-support-engineer",
        "ats":        "greenhouse",
        "job_type":   "Full-time",
        "experience": "Mid-level",
        "status":     "viewed",
        "days_ago":   2,
    },
    {
        "id":         "demo_004",
        "company":    "Datadog",
        "title":      "Solutions Engineer, EMEA",
        "location":   "Dublin, Ireland",
        "url":        "https://careers.datadoghq.com/detail/solutions-engineer-emea",
        "ats":        "workable",
        "job_type":   "Full-time",
        "experience": "Senior",
        "status":     "applied",
        "days_ago":   3,
    },
    {
        "id":         "demo_005",
        "company":    "Pleo",
        "title":      "Customer Success Manager",
        "location":   "Copenhagen, Denmark",
        "url":        "https://boards.greenhouse.io/pleo/jobs/customer-success-manager",
        "ats":        "greenhouse",
        "job_type":   "Full-time",
        "experience": "Mid-level",
        "status":     "applied",
        "days_ago":   4,
    },
    {
        "id":         "demo_006",
        "company":    "Workday",
        "title":      "Implementation Consultant, Financials",
        "location":   "Remote, UK",
        "url":        "https://workday.wd5.myworkdayjobs.com/implementation-consultant-financials",
        "ats":        "workday",
        "job_type":   "Full-time",
        "experience": "Senior",
        "status":     "new",
        "days_ago":   1,
    },
    {
        "id":         "demo_007",
        "company":    "Zendesk",
        "title":      "Technical Support Specialist",
        "location":   "Dublin, Ireland",
        "url":        "https://jobs.zendesk.com/technical-support-specialist-dublin",
        "ats":        "lever",
        "job_type":   "Full-time",
        "experience": "Junior",
        "status":     "not applied",
        "days_ago":   5,
    },
    {
        "id":         "demo_008",
        "company":    "Adyen",
        "title":      "Implementation Engineer",
        "location":   "Amsterdam, Netherlands",
        "url":        "https://careers.adyen.com/vacancies/implementation-engineer",
        "ats":        "ashby",
        "job_type":   "Full-time",
        "experience": "Mid-level",
        "status":     "viewed",
        "days_ago":   2,
    },
    {
        "id":         "demo_009",
        "company":    "HubSpot",
        "title":      "Customer Onboarding Specialist",
        "location":   "Remote, EMEA",
        "url":        "https://www.hubspot.com/careers/jobs/customer-onboarding-specialist-emea",
        "ats":        "greenhouse",
        "job_type":   "Full-time",
        "experience": "Junior",
        "status":     "mismatched",
        "days_ago":   6,
    },
    {
        "id":         "demo_010",
        "company":    "Figma",
        "title":      "Solutions Engineer, Enterprise EMEA",
        "location":   "London, UK",
        "url":        "https://boards.greenhouse.io/figma/jobs/solutions-engineer-enterprise-emea",
        "ats":        "greenhouse",
        "job_type":   "Full-time",
        "experience": "Senior",
        "status":     "new",
        "days_ago":   0,
    },
    {
        "id":         "demo_011",
        "company":    "Personio",
        "title":      "Onboarding Manager",
        "location":   "Munich, Germany",
        "url":        "https://www.personio.com/about-personio/jobs/onboarding-manager",
        "ats":        "personio",
        "job_type":   "Full-time",
        "experience": "Mid-level",
        "status":     "new",
        "days_ago":   1,
    },
    {
        "id":         "demo_012",
        "company":    "Klarna",
        "title":      "Technical Support Lead",
        "location":   "Stockholm, Sweden",
        "url":        "https://jobs.lever.co/klarna/technical-support-lead",
        "ats":        "lever",
        "job_type":   "Full-time",
        "experience": "Senior",
        "status":     "applied",
        "days_ago":   7,
    },
]

# ── Audit log entries — make the pipeline look used ───────────────────────────
DEMO_AUDIT = [
    ("demo_003", "viewed",      2),
    ("demo_004", "viewed",      4),
    ("demo_004", "applied",     3),
    ("demo_005", "viewed",      5),
    ("demo_005", "applied",     4),
    ("demo_007", "viewed",      6),
    ("demo_007", "not applied", 5),
    ("demo_008", "viewed",      3),
    ("demo_009", "viewed",      7),
    ("demo_009", "mismatched",  6),
    ("demo_012", "viewed",      8),
    ("demo_012", "applied",     7),
]


def get_connection():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL not set. Add it to your .env file.")
        sys.exit(1)
    return psycopg2.connect(url)


def reset_demo(cur):
    ids = tuple(j["id"] for j in DEMO_JOBS)
    cur.execute("DELETE FROM audit_log WHERE job_id IN %s", (ids,))
    cur.execute("DELETE FROM jobs WHERE id IN %s", (ids,))
    print(f"  Cleared {len(DEMO_JOBS)} demo jobs and their audit entries.")


def seed_jobs(cur):
    now = datetime.utcnow()
    inserted = 0
    for job in DEMO_JOBS:
        date_found = now - timedelta(days=job["days_ago"])
        cur.execute("""
            INSERT INTO jobs
                (id, company, title, location, url, ats_source, job_type, experience, status, date_found)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            job["id"], job["company"], job["title"], job["location"],
            job["url"], job["ats"], job["job_type"], job["experience"],
            job["status"], date_found,
        ))
        if cur.rowcount:
            inserted += 1
            print(f"  + {job['company']:20s}  {job['title']}")
    print(f"\n  {inserted} jobs inserted ({len(DEMO_JOBS) - inserted} already existed, skipped).")
    return inserted


def seed_audit(cur):
    now = datetime.utcnow()
    for job_id, new_status, days_ago in DEMO_AUDIT:
        changed_at = now - timedelta(days=days_ago)
        cur.execute("""
            INSERT INTO audit_log (job_id, new_status, ip, changed_at)
            VALUES (%s, %s, %s, %s)
        """, (job_id, new_status, "demo", changed_at))
    print(f"  {len(DEMO_AUDIT)} audit log entries written.")


def main():
    parser = argparse.ArgumentParser(description="Seed Job Radar with demo data.")
    parser.add_argument("--reset", action="store_true",
                        help="Remove existing demo jobs before re-inserting.")
    args = parser.parse_args()

    print("\nJob Radar — Demo Seeder")
    print("─" * 40)

    conn = get_connection()
    cur = conn.cursor()

    if args.reset:
        print("\nResetting demo data...")
        reset_demo(cur)

    print("\nInserting demo jobs...")
    seed_jobs(cur)

    print("\nWriting audit history...")
    seed_audit(cur)

    conn.commit()
    cur.close()
    conn.close()

    print("\n✓ Done. Open your dashboard to see the demo pipeline.")
    print("  To reset and re-seed: python seed_demo.py --reset\n")


if __name__ == "__main__":
    main()
