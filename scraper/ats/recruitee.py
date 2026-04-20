import httpx
from .utils import make_id, infer_experience, infer_job_type

async def fetch_jobs(company_slug: str, company_name: str) -> list:
    url = f"https://{company_slug}.recruitee.com/api/offers"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    jobs = []
    for job in data.get("offers", []):
        job_url = job.get("careers_url", "")
        title = job.get("title", "")
        if not job_url:
            continue
        jobs.append({
            "id": make_id(job_url),
            "company": company_name,
            "title": title,
            "location": job.get("location", "Remote"),
            "url": job_url,
            "ats": "recruitee",
            "job_type": infer_job_type(job.get("employment_type_code", "")),
            "experience": infer_experience(title),
        })
    return jobs