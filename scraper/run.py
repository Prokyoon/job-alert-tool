import asyncio
import yaml
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scraper.ats import (
    greenhouse, lever, generic,
    workable, ashby, bamboohr, personio,
    smartrecruiters, teamtailor, recruitee, pinpoint
)
from scraper.filters import is_relevant
from db.database import init_db, job_exists, insert_job, cleanup_old_jobs
from bot.telegram_bot import notify

COMPANIES_PATH = os.path.join(os.path.dirname(__file__), "companies.yaml")

ATS_MAP = {
    "greenhouse":      lambda c, n: greenhouse.fetch_jobs(c["slug"], n),
    "lever":           lambda c, n: lever.fetch_jobs(c["slug"], n),
    "workable":        lambda c, n: workable.fetch_jobs(c["slug"], n),
    "ashby":           lambda c, n: ashby.fetch_jobs(c["slug"], n),
    "bamboohr":        lambda c, n: bamboohr.fetch_jobs(c["slug"], n),
    "personio":        lambda c, n: personio.fetch_jobs(c["slug"], n),
    "smartrecruiters": lambda c, n: smartrecruiters.fetch_jobs(c["slug"], n),
    "teamtailor":      lambda c, n: teamtailor.fetch_jobs(c["slug"], n),
    "recruitee":       lambda c, n: recruitee.fetch_jobs(c["slug"], n),
    "pinpoint":        lambda c, n: pinpoint.fetch_jobs(c["slug"], n),
    "generic":         lambda c, n: generic.fetch_jobs(c["url"], n, c.get("selector", "a")),
}

async def run():
    init_db()
    cleanup_old_jobs()

    with open(COMPANIES_PATH) as f:
        config = yaml.safe_load(f)

    for company in config["companies"]:
        name = company["name"]
        ats = company["ats"]
        print(f"Checking {name}...")

        fetcher = ATS_MAP.get(ats)
        if not fetcher:
            print(f"  Unknown ATS '{ats}' — skipping")
            continue

        try:
            jobs = await fetcher(company, name)
        except Exception as e:
            print(f"  Error scraping {name}: {e}")
            continue

        new_count = 0
        for job in jobs:
            if not is_relevant(job):
                continue
            if job_exists(job["id"]):
                continue
            insert_job(job)
            await notify(job)
            new_count += 1
            print(f"  New job: {job['title']} at {name}")

        if new_count == 0:
            print(f"  No new relevant jobs")

    print("Scrape complete.")

if __name__ == "__main__":
    asyncio.run(run())