import asyncio
import yaml
import sys
import os
 
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
 
from scraper.ats import greenhouse, lever, generic
from db.database import init_db, job_exists, insert_job, cleanup_old_jobs
from bot.telegram_bot import notify
 
async def run():
    init_db()
    cleanup_old_jobs()
 
    with open('scraper/companies.yaml') as f:
        config = yaml.safe_load(f)
 
    for company in config['companies']:
        name = company['name']
        ats = company['ats']
        print(f'Checking {name}...')
 
        try:
            if ats == 'greenhouse':
                jobs = await greenhouse.fetch_jobs(company['slug'], name)
            elif ats == 'lever':
                jobs = await lever.fetch_jobs(company['slug'], name)
            else:
                jobs = await generic.fetch_jobs(
                    company['url'], name,
                    company.get('selector', 'a')
                )
        except Exception as e:
            print(f'Error scraping {name}: {e}')
            continue
 
        for job in jobs:
            if not job_exists(job['id']):
                insert_job(job)
                notify(job)
                print(f'  New job: {job["title"]} at {name}')
 
    print('Scrape complete.')
 
if __name__ == '__main__':
    asyncio.run(run())