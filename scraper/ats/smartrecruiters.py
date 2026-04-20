import httpx
from .utils import make_id, infer_experience, infer_job_type

async def fetch_jobs(company_slug: str, company_name: str) -> list:
    url = f"https://api.smartrecruiters.com/v1/companies/{company_slug}/postings"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    jobs = []
    for job in data.get("content", []):
        job_url = f"https://jobs.smartrecruiters.com/{company_slug}/{job.get('id', '')}"
        title = job.get("name", "")
        loc = job.get("location", {})
        location = ", ".join(filter(None, [loc.get("city"), loc.get("country")]))
        jobs.append({
            "id": make_id(job_url),
            "company": company_name,
            "title": title,
            "location": location or "Remote",
            "url": job_url,
            "ats": "smartrecruiters",
            "job_type": infer_job_type(job.get("typeOfEmployment", {}).get("label", "")),
            "experience": infer_experience(title),
        })
    return jobs