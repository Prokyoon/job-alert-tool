import yaml
import re

with open("filters.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

INCLUDE = [kw.lower() for kw in config.get("include_keywords", [])]
EXCLUDE = [kw.lower() for kw in config.get("exclude_keywords", [])]

def is_relevant(job: dict) -> bool:
    title = job.get("title", "").lower()

    # Must match at least one include keyword
    if not any(kw in title for kw in INCLUDE):
        return False

    # Must not match any exclude keyword
    if any(kw in title for kw in EXCLUDE):
        return False

    return True