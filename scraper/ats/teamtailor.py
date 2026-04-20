import httpx
from .utils import make_id, infer_experience, infer_job_type

async def fetch_jobs(company_slug: str, company_name: str) -> list:
    url = f"https://api.teamtailor.com/v1/jobs?filter[status]=published"
    headers = {
        "Authorization": "Token token=TEAMTAILOR_PUBLIC",
        "X-Api-Version": "20210218",
        "Career-Site": company_slug,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    jobs = []
    for job in data.get("data", []):
        attrs = job.get("attributes", {})
        job_url = attrs.get("career-site-url", "")
        title = attrs.get("title", "")
        if not job_url:
            continue
        jobs.append({
            "id": make_id(job_url),
            "company": company_name,
            "title": title,
            "location": attrs.get("remote-status", "On-site"),
            "url": job_url,
            "ats": "teamtailor",
            "job_type": infer_job_type(attrs.get("employment-type", "")),
            "experience": infer_experience(title),
        })
    return jobs