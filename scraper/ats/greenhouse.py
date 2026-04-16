import httpx
import hashlib
 
async def fetch_jobs(company_slug: str, company_name: str) -> list:
    url = f'https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs'
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    jobs = []
    for job in data.get('jobs', []):
        job_url = job.get('absolute_url', '')
        jobs.append({
            'id': hashlib.md5(job_url.encode()).hexdigest(),
            'company': company_name,
            'title': job.get('title', ''),
            'location': job.get('location', {}).get('name', 'Remote'),
            'url': job_url,
            'ats': 'greenhouse',
        })
    return jobs