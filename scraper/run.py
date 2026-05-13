import asyncio
import yaml
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from greenhouse import fetch_jobs as greenhouse_fetch
from lever import fetch_jobs as lever_fetch
from workable import fetch_jobs as workable_fetch
from ashby import fetch_jobs as ashby_fetch
from bamboohr import fetch_jobs as bamboohr_fetch
from personio import fetch_jobs as personio_fetch
from smartrecruiters import fetch_jobs as smartrecruiters_fetch
from teamtailor import fetch_jobs as teamtailor_fetch
from recruitee import fetch_jobs as recruitee_fetch
from pinpoint import fetch_jobs as pinpoint_fetch
from generic import fetch_jobs as generic_fetch
from filters import is_relevant
from database import init_db, job_exists, insert_job, cleanup_old_jobs
from telegram_bot import notify

COMPANIES_PATH = os.path.join(os.path.dirname(__file__), "companies.yaml")

ATS_MAP = {
    "greenhouse":      lambda c, n: greenhouse_fetch(c["slug"], n),
    "lever":           lambda c, n: lever_fetch(c["slug"], n),
    "workable":        lambda c, n: workable_fetch(c["slug"], n),
    "ashby":           lambda c, n: ashby_fetch(c["slug"], n),
    "bamboohr":        lambda c, n: bamboohr_fetch(c["slug"], n),
    "personio":        lambda c, n: personio_fetch(c["slug"], n),
    "smartrecruiters": lambda c, n: smartrecruiters_fetch(c["slug"], n),
    "teamtailor":      lambda c, n: teamtailor_fetch(c["slug"], n),
    "recruitee":       lambda c, n: recruitee_fetch(c["slug"], n),
    "pinpoint":        lambda c, n: pinpoint_fetch(c["slug"], n),
    "generic":         lambda c, n: generic_fetch(c["url"], n, c.get("selector", "a")),
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