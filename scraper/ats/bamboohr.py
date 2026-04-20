import httpx
from xml.etree import ElementTree
from .utils import make_id, infer_experience

async def fetch_jobs(company_slug: str, company_name: str) -> list:
    url = f"https://{company_slug}.bamboohr.com/jobs/feed.php"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            return []
    jobs = []
    try:
        root = ElementTree.fromstring(resp.text)
        for item in root.findall(".//item"):
            job_url = item.findtext("link", "")
            title = item.findtext("title", "")
            location = item.findtext("location", "Remote")
            if not job_url:
                continue
            jobs.append({
                "id": make_id(job_url),
                "company": company_name,
                "title": title,
                "location": location,
                "url": job_url,
                "ats": "bamboohr",
                "job_type": "Full-time",
                "experience": infer_experience(title),
            })
    except Exception:
        pass
    return jobs