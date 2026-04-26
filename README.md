# Job Radar

A self-hosted job monitoring system that watches 30+ companies across 10 ATS platforms, filters for relevant roles in Europe/Remote, and delivers real-time Telegram notifications — with a personal ops dashboard to track your application pipeline.

Built for job search across RegTech, FinTech, and enterprise SaaS companies.

---

## What it does

1. **Scraper** — polls the careers pages of configured companies every N hours via their ATS APIs (Greenhouse, Lever, Workable, Ashby, BambooHR, Personio, SmartRecruiters, TeamTailor, Recruitee, Pinpoint, and generic HTML scraping).
2. **Filter** — drops jobs that don't match your role keywords, are in excluded locations (US/Canada/APAC), or are in a non-English/Romanian language (detected via `langdetect` + non-Latin script regex).
3. **Notify** — sends new relevant jobs to Telegram instantly.
4. **Dashboard** — a FastAPI web app to manage your pipeline: mark jobs as New / Viewed / Applied / Not Applied / Mismatched, search and filter, and export to CSV.
5. **Audit log** — every status change is recorded with a timestamp and IP.
6. **Stats page** — live metrics: companies monitored, ATS coverage, pipeline breakdown, jobs found per day.

---

## Architecture

```
scraper/run.py  ──►  ATS APIs  ──►  filters.py  ──►  PostgreSQL (Supabase)
                                                            │
                                                     Telegram bot notify
                                                            │
                                                      web/app.py (FastAPI)
                                                            │
                                              ┌─────────────────────────┐
                                              │  /          dashboard    │
                                              │  /stats     metrics      │
                                              │  /audit     audit log    │
                                              │  /export    CSV download │
                                              │  /health    JSON status  │
                                              └─────────────────────────┘
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Scraper | Python + httpx + asyncio |
| ATS support | Greenhouse, Lever, Workable, Ashby, BambooHR, Personio, SmartRecruiters, TeamTailor, Recruitee, Pinpoint, Generic HTML |
| Language detection | langdetect + regex heuristics |
| Database | PostgreSQL via Supabase |
| Web framework | FastAPI + Jinja2 + Tailwind CSS |
| Auth | Cookie-based session (itsdangerous, 8h expiry) |
| Notifications | Telegram Bot API |
| Hosting | Render (web service + cron job) |
| Rate limiting | slowapi |

---

## Project structure

```
├── scraper/
│   ├── ats/              # One module per ATS platform
│   │   ├── greenhouse.py
│   │   ├── lever.py
│   │   ├── workable.py
│   │   ├── ashby.py
│   │   ├── bamboohr.py
│   │   ├── personio.py
│   │   ├── smartrecruiters.py
│   │   ├── teamtailor.py
│   │   ├── recruitee.py
│   │   ├── pinpoint.py
│   │   └── generic.py
│   ├── filters.py        # Keyword + location + language filtering
│   └── run.py            # Entrypoint — runs the scrape loop
├── db/
│   └── database.py       # All DB queries (jobs, audit log, stats, export)
├── web/
│   ├── app.py            # FastAPI routes + auth + middleware
│   └── templates/
│       ├── index.html    # Job dashboard
│       ├── stats.html    # Pipeline metrics
│       ├── audit.html    # Audit log
│       └── login.html    # Login page
├── bot/
│   └── telegram_bot.py   # Telegram notification formatting
├── companies.yaml        # List of companies to monitor (add new ones here)
├── filters.yaml          # Role keywords, location include/exclude lists
├── render.yaml           # Render deployment config
└── requirements.txt
```

---

## Adding a new company

Open `companies.yaml` and add an entry. No code changes needed.

```yaml
companies:
  - name: Stripe
    ats: greenhouse
    slug: stripe

  - name: Revolut
    ats: lever
    slug: revolut

  # Generic HTML scraper (for companies without a standard ATS)
  - name: SomeCompany
    ats: generic
    url: https://somecompany.com/careers
    selector: "a[href*='job']"
```

**Supported ATS values:** `greenhouse`, `lever`, `workable`, `ashby`, `bamboohr`, `personio`, `smartrecruiters`, `teamtailor`, `recruitee`, `pinpoint`, `generic`

---

## Adding a new role keyword

Open `filters.yaml` and add to `include_keywords`. Keywords are matched as whole-phrase substrings (case-insensitive) against the job title.

```yaml
include_keywords:
  - Technical Support Specialist
  - Customer Success Manager
  - Solutions Engineer
  - Your New Role Here     # ← add here
```

---

## Local setup

### Prerequisites
- Python 3.11+
- PostgreSQL database (or a free Supabase project)
- Telegram bot token (from @BotFather)

### Steps

```bash
# 1. Clone and install
git clone https://github.com/yourname/job-radar
cd job-radar
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your values (see Environment variables section)

# 3. Initialise the database
python -c "from db.database import init_db; init_db()"

# 4. Run a scrape
python scraper/run.py

# 5. Start the dashboard
uvicorn web.app:app --reload --port 8000
# Open http://localhost:8000
```

---

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (e.g. from Supabase) |
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat/user ID |
| `SECRET_KEY` | Random secret for session signing (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DASHBOARD_USER` | Login username for the dashboard |
| `DASHBOARD_PASS` | Login password for the dashboard |

---

## Deploying to Render

1. Push this repo to GitHub.
2. In Render, create a **Web Service** pointing to the repo.
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn web.app:app --host 0.0.0.0 --port $PORT`
3. Create a **Cron Job** in Render pointing to the same repo.
   - Command: `python scraper/run.py`
   - Schedule: `0 */4 * * *` (every 4 hours)
4. Add all environment variables under **Environment** in both services.

---

## Dashboard endpoints

| Route | Description |
|---|---|
| `GET /` | Job dashboard with search, filter, pagination |
| `GET /stats` | Pipeline metrics — companies monitored, ATS breakdown, daily chart |
| `GET /audit` | Audit log — every status change with timestamp and IP |
| `GET /export?status=applied` | CSV download (filter by status, or omit for all) |
| `GET /health` | JSON health check — DB connectivity + job counts |
| `GET /login` | Login page |
| `GET /logout` | Clear session |

---

## Security

- Session cookies are `httponly`, `samesite=lax`, `secure=True` (HTTPS only), expire after 8 hours.
- All mutation routes are rate-limited to 500 requests/minute per IP.
- Bulk status updates are capped at 200 jobs per request.
- Search input is capped at 100 characters via FastAPI `Query(max_length=100)`.
- HTTP security headers on every response: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Content-Security-Policy`.
- All status changes are recorded in the `audit_log` table.
- Credentials and secrets are environment variables — never committed to the repo.

---

## Database schema

```sql
-- Jobs
CREATE TABLE jobs (
    id          TEXT PRIMARY KEY,
    company     TEXT NOT NULL,
    title       TEXT NOT NULL,
    location    TEXT,
    url         TEXT NOT NULL,
    ats_source  TEXT,
    date_found  TIMESTAMP NOT NULL DEFAULT NOW(),
    status      TEXT DEFAULT 'new',   -- new | viewed | applied | not applied | mismatched
    job_type    TEXT,
    experience  TEXT
);

-- Audit log
CREATE TABLE audit_log (
    id          SERIAL PRIMARY KEY,
    job_id      TEXT NOT NULL,
    new_status  TEXT NOT NULL,
    changed_at  TIMESTAMP DEFAULT NOW(),
    ip          TEXT
);

-- Recommended index
CREATE INDEX idx_jobs_status_date ON jobs (status, date_found DESC);
```