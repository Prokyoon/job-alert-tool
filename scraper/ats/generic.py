import hashlib
from playwright.async_api import async_playwright
 
async def fetch_jobs(careers_url: str, company_name: str,
                     job_selector: str = 'a') -> list:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(careers_url, wait_until='networkidle', timeout=30000)
        links = await page.query_selector_all(job_selector)
        jobs = []
        for link in links:
            title = await link.inner_text()
            href = await link.get_attribute('href')
            if not href or len(title.strip()) < 5:
                continue
            if not href.startswith('http'):
                href = careers_url.rstrip('/') + '/' + href.lstrip('/')
            jobs.append({
                'id': hashlib.md5(href.encode()).hexdigest(),
                'company': company_name,
                'title': title.strip(),
                'location': 'See listing',
                'url': href,
                'ats': 'generic',
            })
        await browser.close()
    return jobs