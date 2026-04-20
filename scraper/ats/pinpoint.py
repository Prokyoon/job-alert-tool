import httpx
from .utils import make_id, infer_experience, infer_job_type

async def fetch_jobs(company_slug: str, company_name: str) -> list:
    url = f"https://{company_slug}.pinpointhq.com/api/v1/jobs"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    jobs = []
    for job in data.get("data", []):
        attrs = job.get("attributes", {})
        job_url = attrs.get("show_url", "")
        title = attrs.get("title", "")
        if not job_url:
            continue
        jobs.append({
            "id": make_id(job_url),
            "company": company_name,
            "title": title,
            "location": attrs.get("location_name", "Remote"),
            "url": job_url,
            "ats": "pinpoint",
            "job_type": infer_job_type(attrs.get("job_type", "")),
            "experience": infer_experience(title),
        })
    return jobs