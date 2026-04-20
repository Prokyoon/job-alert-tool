import httpx
from xml.etree import ElementTree
from .utils import make_id, infer_experience, infer_job_type

async def fetch_jobs(company_slug: str, company_name: str) -> list:
    url = f"https://{company_slug}.jobs.personio.com/xml"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            return []
    jobs = []
    try:
        root = ElementTree.fromstring(resp.text)
        for pos in root.findall(".//position"):
            job_url = pos.findtext("url", "")
            title = pos.findtext("name", "")
            location = pos.findtext("office", "Remote")
            job_type = pos.findtext("schedule", "")
            if not job_url:
                continue
            jobs.append({
                "id": make_id(job_url),
                "company": company_name,
                "title": title,
                "location": location,
                "url": job_url,
                "ats": "personio",
                "job_type": infer_job_type(job_type),
                "experience": infer_experience(title),
            })
    except Exception:
        pass
    return jobs