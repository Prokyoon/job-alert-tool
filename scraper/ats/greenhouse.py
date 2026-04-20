import httpx
from .utils import make_id, infer_experience, infer_job_type

async def fetch_jobs(company_slug: str, company_name: str) -> list:
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    jobs = []
    for job in data.get("jobs", []):
        job_url = job.get("absolute_url", "")
        if not job_url:
            continue
        # Greenhouse returns employment_type in metadata array
        job_type = None
        for meta in job.get("metadata", []):
            if meta.get("name", "").lower() in ("employment type", "job type", "contract type"):
                job_type = infer_job_type(str(meta.get("value", "")))
                break
        title = job.get("title", "")
        jobs.append({
            "id": make_id(job_url),
            "company": company_name,
            "title": title,
            "location": job.get("location", {}).get("name", "Remote"),
            "url": job_url,
            "ats": "greenhouse",
            "job_type": job_type or "Full-time",
            "experience": infer_experience(title),
        })
    return jobs