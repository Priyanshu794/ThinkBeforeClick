# Phase 4: Google Safe Browsing lookup + WHOIS domain-age check
# Phase 4: Google Safe Browsing lookup + WHOIS domain-age check
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import requests

try:
    import whois as whois_lib
except ImportError:
    whois_lib = None

from app.core.config import settings

SAFE_BROWSING_ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
REQUEST_TIMEOUT_SECONDS = 5
NEW_DOMAIN_THRESHOLD_DAYS = 180


def _extract_domain(url: str) -> Optional[str]:
    if not url:
        return None
    domain = re.sub(r"^https?://", "", url.lower()).split("/")[0]
    domain = domain.split(":")[0]  # strip port if present
    return domain or None


# ---------------------------------------------------------------------------
# GOOGLE SAFE BROWSING
# ---------------------------------------------------------------------------

def check_safe_browsing(url: str) -> Tuple[int, List[str]]:
    if not url:
        return 0, []

    api_key = settings.SAFE_BROWSING_API_KEY
    if not api_key:
        return 0, ["Safe Browsing check skipped: no API key configured"]

    body = {
        "client": {"clientId": "thinkbeforeclick", "clientVersion": "0.1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }

    try:
        resp = requests.post(
            SAFE_BROWSING_ENDPOINT,
            params={"key": api_key},
            json=body,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json()
        matches = data.get("matches", [])
        if matches:
            threat_types = sorted({m.get("threatType", "UNKNOWN") for m in matches})
            return 40, [f"Google Safe Browsing flagged this URL ({', '.join(threat_types)})"]
        return 0, []
    except requests.exceptions.Timeout:
        return 0, ["Safe Browsing check timed out — skipped"]
    except requests.exceptions.RequestException as e:
        return 0, [f"Safe Browsing check failed — skipped ({type(e).__name__})"]


# ---------------------------------------------------------------------------
# WHOIS DOMAIN AGE
# ---------------------------------------------------------------------------

def check_domain_age(url: str) -> Tuple[int, List[str]]:
    if not url:
        return 0, []

    if whois_lib is None:
        return 0, ["WHOIS check skipped: python-whois not installed"]

    domain = _extract_domain(url)
    if not domain:
        return 0, []

    try:
        w = whois_lib.whois(domain)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0] if creation_date else None
        if not creation_date:
            return 0, ["WHOIS lookup returned no creation date — skipped"]

        if creation_date.tzinfo is None:
            creation_date = creation_date.replace(tzinfo=timezone.utc)

        age_days = (datetime.now(timezone.utc) - creation_date).days
        if age_days < 0:
            return 0, ["WHOIS returned an implausible creation date — skipped"]

        if age_days < NEW_DOMAIN_THRESHOLD_DAYS:
            return 20, [f"Domain registered recently ({age_days} days ago) — common phishing pattern"]
        return 0, []
    except Exception as e:
        # WHOIS servers are flaky/rate-limited/vary by TLD — never let this break /analyze
        return 0, [f"WHOIS lookup failed — skipped ({type(e).__name__})"]


# ---------------------------------------------------------------------------
# COMBINED THREAT-INTEL RESULT (Phase 4 only — not fused with rules/ML yet)
# ---------------------------------------------------------------------------

def run_threat_intel(url: Optional[str] = None) -> dict:
    sb_score, sb_flags = check_safe_browsing(url) if url else (0, [])
    whois_score, whois_flags = check_domain_age(url) if url else (0, [])

    total_score = sb_score + whois_score
    all_flags = sb_flags + whois_flags
    label = "Flagged" if total_score > 0 else ("Clean" if url else "Not checked")

    return {
        "threat_score": total_score,
        "threat_label": label,
        "threat_flags": all_flags,
    }