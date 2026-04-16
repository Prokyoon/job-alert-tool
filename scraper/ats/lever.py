import httpx
import hashlib
 
async def fetch_jobs(company_slug: str, company_name: str) -> list:
    url = f'https://api.lever.co/v0/postings/{company_slug}?mode=json'
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    jobs = []
    for job in data:
        job_url = job.get('hostedUrl', '')
        location = job.get('categories', {}).get('location', 'Remote')
        jobs.append({
            'id': hashlib.md5(job_url.encode()).hexdigest(),
            'company': company_name,
            'title': job.get('text', ''),
            'location': location,
            'url': job_url,
            'ats': 'lever',
        })
    return jobs