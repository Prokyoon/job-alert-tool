import httpx
from .utils import make_id, infer_experience, infer_job_type

async def fetch_jobs(company_slug: str, company_name: str) -> list:
    url = f"https://apply.workable.com/api/v3/accounts/{company_slug}/jobs"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"query": "", "location": []}, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    jobs = []
    for job in data.get("results", []):
        job_url = f"https://apply.workable.com/{company_slug}/j/{job.get('shortcode', '')}"
        title = job.get("title", "")
        jobs.append({
            "id": make_id(job_url),
            "company": company_name,
            "title": title,
            "location": job.get("location", {}).get("city", "Remote") + (
                f", {job.get('location', {}).get('country', '')}" if job.get("location", {}).get("country") else ""
            ),
            "url": job_url,
            "ats": "workable",
            "job_type": infer_job_type(job.get("employment_type", "")),
            "experience": infer_experience(title),
        })
    return jobs