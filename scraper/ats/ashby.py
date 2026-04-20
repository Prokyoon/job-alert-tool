import httpx
from .utils import make_id, infer_experience, infer_job_type

async def fetch_jobs(company_slug: str, company_name: str) -> list:
    url = f"https://api.ashbyhq.com/posting-public/job-board/{company_slug}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    jobs = []
    for job in data.get("jobPostings", []):
        job_url = job.get("jobPostingUrls", {}).get("careerPage", "")
        if not job_url:
            continue
        title = job.get("title", "")
        jobs.append({
            "id": make_id(job_url),
            "company": company_name,
            "title": title,
            "location": job.get("locationName", "Remote"),
            "url": job_url,
            "ats": "ashby",
            "job_type": infer_job_type(job.get("employmentType", "")),
            "experience": infer_experience(title),
        })
    return jobs