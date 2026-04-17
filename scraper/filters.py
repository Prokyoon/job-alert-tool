def is_relevant(job: dict) -> bool:
    title = job.get("title", "").lower()
    location = job.get("location", "").lower()

    # Must match at least one include keyword in title
    if not any(kw in title for kw in INCLUDE):
        return False

    # Exclude if title requires a blocked language
    if has_blocked_language(job.get("title", "")):
        return False

    # Hard exclude blocked locations — checked BEFORE include list
    # This catches "Remote, USA", "Remote - United States" etc.
    if any(kw in location for kw in LOCATION_EXCLUDE):
        return False

    # Must match at least one allowed region
    # Skip check if location is empty or unparseable
    if location and location not in ("remote", "see listing", "worldwide", "global", ""):
        if LOCATION_INCLUDE and not any(kw in location for kw in LOCATION_INCLUDE):
            return False

    return True