import yaml
import re
import os

FILTERS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "filters.yaml")

with open(FILTERS_PATH, encoding="utf-8") as f:
    config = yaml.safe_load(f)

# All keywords are matched as whole-word substrings against the job title
INCLUDE = [kw.lower() for kw in config.get("include_keywords", [])]
LOCATION_INCLUDE = [kw.lower() for kw in config.get("location_keywords", [])]
LOCATION_EXCLUDE = [kw.lower() for kw in config.get("location_exclude", [])]

# ── Language detection ────────────────────────────────────────────────────────
# Strategy: use langdetect if available, fall back to a character-script
# heuristic. Jobs are accepted only if detected as English or Romanian.
# If detection is uncertain we default to ACCEPT (don't block good jobs).

ALLOWED_LANG_CODES = {"en", "ro"}  # ISO 639-1

# Non-Latin script ranges — a title with these characters is almost certainly
# not English or Romanian, so we can reject immediately without langdetect.
NON_LATIN_RE = re.compile(
    r"[\u0400-\u04FF"   # Cyrillic
    r"\u0370-\u03FF"   # Greek
    r"\u0600-\u06FF"   # Arabic
    r"\u0590-\u05FF"   # Hebrew
    r"\u4E00-\u9FFF"   # CJK (Chinese / Japanese kanji)
    r"\u3040-\u30FF"   # Hiragana / Katakana
    r"\uAC00-\uD7AF"   # Korean Hangul
    r"]"
)

# Common non-English/Romanian language indicators that appear in job titles
# as explicit language requirements (e.g. "Fluent French required").
LANGUAGE_REQUIREMENT_RE = re.compile(
    r"\b("
    r"french|deutsch|german|spanish|espanol|italian|italiano"
    r"|portuguese|portugues|dutch|nederlands|swedish|svenska"
    r"|danish|dansk|finnish|suomi|norwegian|norsk|polish|polski"
    r"|czech|slovak|hungarian|greek|turkish|arabic|hebrew"
    r"|russian|ukrainian|mandarin|cantonese|japanese|korean"
    r")\b",
    re.IGNORECASE,
)

try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False


def _detect_language(text: str):
    """Return ISO 639-1 language code or None if detection fails."""
    if not LANGDETECT_AVAILABLE:
        return None
    try:
        return detect(text)
    except Exception:
        return None


def is_non_english_romanian(title: str) -> bool:
    """
    Return True if the job title is detectably NOT in English or Romanian.
    When in doubt (detection uncertain), return False so the job is kept.
    """
    # 1. Hard reject: non-Latin script characters
    if NON_LATIN_RE.search(title):
        return True

    # 2. Hard reject: explicit language requirement keyword in title
    if LANGUAGE_REQUIREMENT_RE.search(title):
        return True

    # 3. Soft reject via langdetect (only when confident)
    lang = _detect_language(title)
    if lang and lang not in ALLOWED_LANG_CODES:
        return True

    return False


# ── Title matching ────────────────────────────────────────────────────────────

def _title_matches(title_lower: str) -> bool:
    """True if the job title contains one of the include keywords as a phrase."""
    for kw in INCLUDE:
        pattern = r"(?<!\w)" + re.escape(kw) + r"(?!\w)"
        if re.search(pattern, title_lower):
            return True
    return False


# ── Main filter ───────────────────────────────────────────────────────────────

def is_relevant(job: dict) -> bool:
    title = job.get("title", "")
    title_lower = title.lower()
    location = job.get("location", "").lower()

    # 1. Title must match an include keyword (exact phrase)
    if not _title_matches(title_lower):
        return False

    # 2. Title must not be detected as a non-English/Romanian language
    if is_non_english_romanian(title):
        return False

    # 3. Location hard-exclude (US/Canada etc.)
    if any(kw in location for kw in LOCATION_EXCLUDE):
        return False

    # 4. Location soft-include (only apply if location is meaningful)
    if location and location not in ("remote", "see listing", "worldwide", "global", ""):
        if LOCATION_INCLUDE and not any(kw in location for kw in LOCATION_INCLUDE):
            return False

    return True