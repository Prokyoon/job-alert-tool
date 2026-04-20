import hashlib
import re

def make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()

def infer_experience(title: str) -> str:
    t = title.lower()
    if any(x in t for x in ["vp ", "vice president", "director", "head of", "chief"]):
        return "Leadership"
    if any(x in t for x in ["principal", "staff", "distinguished"]):
        return "Principal"
    if any(x in t for x in ["senior", "sr.", "sr ", "lead", "team lead"]):
        return "Senior"
    if any(x in t for x in ["junior", "jr.", "jr ", "entry", "graduate", "intern", "apprentice"]):
        return "Junior"
    if any(x in t for x in ["mid", "intermediate", "associate"]):
        return "Mid-level"
    if any(x in t for x in ["manager", "mgr"]):
        return "Manager"
    return "Not specified"

def infer_job_type(raw: str) -> str:
    if not raw:
        return "Not specified"
    r = raw.lower()
    if any(x in r for x in ["full", "permanent", "full-time"]):
        return "Full-time"
    if any(x in r for x in ["part", "part-time"]):
        return "Part-time"
    if any(x in r for x in ["contract", "fixed", "temporary", "temp", "freelance"]):
        return "Contract"
    if "intern" in r:
        return "Internship"
    return raw.strip().title() or "Not specified"