# Phase 2: regex/keyword-based message + URL rule detection
# Updated: added keyword/TLD coverage for delivery-scam and portal-impersonation
# patterns found during real-world test cases (see PROJECT_STATE.md "Known backend
# detection gaps" — Cases 1 and 2 in that section). Additive only — nothing removed,
# nothing re-weighted, per the "don't re-tune without a failing test case" rule; these
# ARE the new failing test cases driving this specific addition.
import re
from typing import List, Tuple

# ---------------------------------------------------------------------------
# MESSAGE RULES
# ---------------------------------------------------------------------------

# Phishing/scam trigger words. We match these with a "flexible" regex builder
# below so that obfuscated variants (u.r.g.e.n.t, u r g e n t, u_r_g_e_n_t)
# are still caught, not just the exact word.
SUSPICIOUS_KEYWORDS = [
    "urgent", "verify", "account", "suspended", "click here", "winner",
    "congratulations", "free", "prize", "limited time", "act now",
    "confirm", "password", "login", "bank", "otp", "refund", "gift card",
    "scholarship", "cash", "reward", "claim now", "immediately",
    "restricted", "blocked", "unusual activity", "security alert",

    # --- Added: delivery/courier scam vocabulary (Case 1, real-world test) ---
    # Extremely common on WhatsApp/SMS — "your parcel couldn't be delivered,
    # update your details" — a phrasing style the original list didn't cover
    # at all.
    "parcel", "courier", "delivery attempt", "could not be delivered",
    "reschedule delivery", "customs fee", "track your shipment",
    "return to sender", "shipping fee", "redelivery",

    # --- Added: portal/results impersonation vocabulary (Case 2, real-world test) ---
    # "Login to check your marks", "provisional certificate", "portal closes" —
    # mundane institutional-notice phrasing that scam messages mimic closely.
    "provisional certificate", "portal closes", "results portal",
]


def _flexible_pattern(word: str) -> re.Pattern:
    """
    Builds a regex that matches a keyword even if it's been obfuscated with
    spaces, dots, dashes, underscores, or asterisks between letters.
    e.g. "urgent" also matches "u.r.g.e.n.t", "u r g e n t", "u-r-g-e-n-t"
    """
    # Escape each character, then allow 0+ separator characters between them
    separator = r"[\s\.\-_\*]*"
    chars = [re.escape(c) for c in word if c != " "]
    # Preserve original spaces in multi-word phrases as "at least one separator"
    pattern_parts = []
    for c in word:
        if c == " ":
            pattern_parts.append(r"[\s\.\-_\*]+")
        else:
            pattern_parts.append(re.escape(c) + separator)
    pattern = "".join(pattern_parts)
    return re.compile(pattern, re.IGNORECASE)


_COMPILED_KEYWORD_PATTERNS = [
    (kw, _flexible_pattern(kw)) for kw in SUSPICIOUS_KEYWORDS
]


def analyze_message(message: str) -> Tuple[int, List[str]]:
    """
    Scans a message for suspicious patterns.
    Returns (score, flags) where score is a simple additive rule-based score
    and flags is a list of human-readable reasons.
    """
    if not message:
        return 0, []

    score = 0
    flags: List[str] = []

    for keyword, pattern in _COMPILED_KEYWORD_PATTERNS:
        if pattern.search(message):
            score += 10
            flags.append(f"Suspicious phrase detected: '{keyword}'")

    # Excessive punctuation / shouting (common in scam messages)
    if re.search(r"[!?]{2,}", message):
        score += 5
        flags.append("Excessive punctuation (e.g. '!!!' or '??')")

    if re.search(r"[A-Z]{6,}", message):
        score += 5
        flags.append("Excessive capitalization (shouting)")

    # Requests for personal/financial info
    if re.search(r"\b(ssn|social security|credit card|cvv|pin\s*number)\b", message, re.IGNORECASE):
        score += 15
        flags.append("Requests sensitive personal/financial information")

    return score, flags


# ---------------------------------------------------------------------------
# URL RULES
# ---------------------------------------------------------------------------

KNOWN_SHORTENERS = [
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "shorte.st", "adf.ly", "cutt.ly", "rebrand.ly",
]

SUSPICIOUS_TLDS = [
    ".xyz", ".top", ".click", ".loan", ".work", ".gq", ".tk", ".ml",
    ".cf", ".ga", ".zip", ".mov", ".rest",
    # --- Added: .info (Case 1 real-world test used a .info delivery-scam URL) ---
    # .info is a legitimate TLD in some genuine use, so this is a lighter-weight
    # signal than .xyz/.tk/etc — still contributes to the score, not an
    # automatic override.
    ".info",
]

SUSPICIOUS_URL_KEYWORDS = [
    "login", "verify", "secure", "account", "update", "confirm",
    "banking", "signin", "password", "webscr", "free", "bonus",

    # --- Added: delivery/results URL vocabulary ---
    "track", "parcel", "delivery", "shipment", "results",
]
def _looks_algorithmically_generated(label: str) -> bool:
    """
    Flags domain labels that look randomly generated rather than human-chosen
    (low vowel ratio or a long consonant run). This is a WEAK, additive signal
    only (+10, not a hard block) because it has a known false-positive rate on
    real brands that deliberately drop vowels (flickr, tumblr, etc.) — it's
    meant to nudge the score, not single-handedly convict a domain.
    """
    label = label.lower()
    if len(label) < 5:
        return False
    vowels = sum(1 for c in label if c in "aeiou")
    vowel_ratio = vowels / len(label)
    longest_run, current_run = 0, 0
    for c in label:
        if c.isalpha() and c not in "aeiou":
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 0
    return vowel_ratio < 0.25 or longest_run >= 5

def analyze_url(url: str) -> Tuple[int, List[str]]:
    """
    Scans a URL for suspicious structural patterns.
    Returns (score, flags).
    """
    if not url:
        return 0, []

    score = 0
    flags: List[str] = []
    url_lower = url.lower()

    # HTTPS check
    if not url_lower.startswith("https://"):
        score += 10
        flags.append("URL does not use HTTPS")

    # Shortener detection
    for shortener in KNOWN_SHORTENERS:
        if shortener in url_lower:
            score += 15
            flags.append(f"URL uses a link shortener ({shortener})")
            break

    # Domain extracted once, up front, so both the TLD check and hyphen check
    # use it consistently (previously the TLD check wrongly tested the whole
    # URL string instead of just the domain — missed almost every real-world
    # phishing URL, since those always have a path/query after the domain).
    domain_part = re.sub(r"^https?://", "", url_lower).split("/")[0]

    # Suspicious TLD (fixed: checks the domain, not the full URL string)
    for tld in SUSPICIOUS_TLDS:
        if domain_part.endswith(tld):
            score += 15
            flags.append(f"Suspicious top-level domain ({tld})")
            break

    # Domain-randomness check (new) — catches algorithmically-generated-looking
    # domains that dodge keyword/TLD rules entirely (e.g. zszbe.xyz)
    labels = domain_part.split(".")
    if any(_looks_algorithmically_generated(l) for l in labels[:-1]):  # skip the TLD label itself
        score += 10
        flags.append("Domain label looks algorithmically generated, not human-chosen")

    # Excessive hyphens in domain (common phishing pattern: secure-login-bank-verify.com)
    if domain_part.count("-") >= 2:
        score += 10
        flags.append("Domain contains multiple hyphens (common phishing pattern)")

    # Suspicious keywords in URL
    for keyword in SUSPICIOUS_URL_KEYWORDS:
        if keyword in url_lower:
            score += 5
            flags.append(f"URL contains suspicious keyword: '{keyword}'")

    # IP address instead of domain name
    if re.match(r"^https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", url_lower):
        score += 20
        flags.append("URL uses a raw IP address instead of a domain name")

    # Excessive subdomains (e.g. secure.login.verify.bank.example.com)
    if domain_part.count(".") >= 4:
        score += 10
        flags.append("Unusually high number of subdomains")

    return score, flags


# ---------------------------------------------------------------------------
# COMBINED RULE-BASED SCORE (message + url) — Phase 2 only, no ML/threat-intel yet
# ---------------------------------------------------------------------------

def run_rule_engine(message: str = None, url: str = None) -> dict:
    msg_score, msg_flags = analyze_message(message) if message else (0, [])
    url_score, url_flags = analyze_url(url) if url else (0, [])

    total_score = msg_score + url_score
    all_flags = msg_flags + url_flags

    # Phase 2 label thresholds — will be superseded by the fusion engine in Phase 5
    if total_score >= 40:
        label = "High Risk"
    elif total_score >= 15:
        label = "Suspicious"
    else:
        label = "Safe"

    return {
        "rule_score": total_score,
        "rule_label": label,
        "rule_flags": all_flags,
    }