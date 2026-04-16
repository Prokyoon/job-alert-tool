import yaml
import re

with open("filters.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

INCLUDE = [kw.lower() for kw in config.get("include_keywords", [])]
BLOCKED_LANGUAGES = [lang.lower() for lang in config.get("blocked_languages", [])]
LOCATION_INCLUDE = [kw.lower() for kw in config.get("location_keywords", [])]
LOCATION_EXCLUDE = [kw.lower() for kw in config.get("location_exclude", [])]

# Patterns that indicate a language requirement in the title
# Matches things like: "French Speaking", "German Speaker",
# "Fluent in Spanish", "Dutch-speaking", "Native Russian"
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

    # Must match at least one include keyword in title
    if not any(kw in title for kw in INCLUDE):
        return False

    # Exclude if title requires a blocked language
    if has_blocked_language(job.get("title", "")):
        return False

    # Location filter
    if LOCATION_INCLUDE:
        if not any(kw in location for kw in LOCATION_INCLUDE):
            return False

    # Exclude blocked locations
    if any(kw in location for kw in LOCATION_EXCLUDE):
        return False

    return True