import yaml
import re
import os

FILTERS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "filters.yaml")

with open(FILTERS_PATH, encoding="utf-8") as f:
    config = yaml.safe_load(f)

INCLUDE = [kw.lower() for kw in config.get("include_keywords", [])]
BLOCKED_LANGUAGES = [lang.lower() for lang in config.get("blocked_languages", [])]
LOCATION_INCLUDE = [kw.lower() for kw in config.get("location_keywords", [])]
LOCATION_EXCLUDE = [kw.lower() for kw in config.get("location_exclude", [])]

LANGUAGE_PATTERNS = [
    r'\b{lang}\b[\s-]*(speaking|speaker|fluent|native|language)?',
    r'(speaking|speaker|fluent in|native)\s+\b{lang}\b',
]

def has_blocked_language(title: str) -> bool:
    title_lower = title.lower()
    for lang in BLOCKED_LANGUAGES:
        for pattern in LANGUAGE_PATTERNS:
            if re.search(pattern.format(lang=re.escape(lang)), title_lower):
                return True
    return False

def is_relevant(job: dict) -> bool:
    title = job.get("title", "").lower()
    location = job.get("location", "").lower()

    if not any(kw in title for kw in INCLUDE):
        return False

    if has_blocked_language(job.get("title", "")):
        return False

    if any(kw in location for kw in LOCATION_EXCLUDE):
        return False

    if location and location not in ("remote", "see listing", "worldwide", "global", ""):
        if LOCATION_INCLUDE and not any(kw in location for kw in LOCATION_INCLUDE):
            return False

    return True