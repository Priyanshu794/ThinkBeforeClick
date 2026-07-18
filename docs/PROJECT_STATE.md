# ThinkBeforeClick — Project State

_Last updated: end of Phase 4, confirmed working._

## Where we are
Phase 1 (Backend Foundation), Phase 2 (Rule-Based Detection Layer), Phase 3 (ML/NLP
Layer), and Phase 4 (Threat-Intelligence Layer) are all complete and verified working.
Ready to begin Phase 5 (Fusion Engine).

## What exists right now
Everything from Phase 1 + 2 + 3 (see below), plus new Phase 4 additions:

- `backend/app/core/config.py` — now implemented (was an empty stub). Loads `.env` via
  `python-dotenv`, exposes a `Settings` object with `SAFE_BROWSING_API_KEY` and
  `DATABASE_URL`.
- `backend/app/services/threat_intel.py` — Phase 4 core logic:
  - `check_safe_browsing(url)` — calls Google Safe Browsing API v4
    (`threatMatches:find`), checks MALWARE / SOCIAL_ENGINEERING / UNWANTED_SOFTWARE /
    POTENTIALLY_HARMFUL_APPLICATION. Returns score 40 + a flag naming the threat type(s)
    if matched, 0 otherwise. Degrades gracefully (returns 0 + explanatory flag) on
    timeout, request failure, or missing API key — never raises.
  - `check_domain_age(url)` — WHOIS lookup via `python-whois`. Domains registered less
    than 180 days ago score 20 + a flag; older domains score 0 silently. Degrades
    gracefully (returns 0 + explanatory flag) if WHOIS fails, times out, or returns no
    creation date — never raises. Known limitation: some domains (e.g. shared
    subdomains like `*.appspot.com`) don't have their own WHOIS record and will always
    hit this graceful-failure path — expected, not a bug.
  - `run_threat_intel(url)` — combines both into `threat_score`, `threat_label`
    (`"Flagged"` / `"Clean"` / `"Not checked"` if no URL provided), `threat_flags`.
- `backend/app/api/analyze.py` — now calls `run_rule_engine()`, `analyze_message_ml()`,
  **and** `run_threat_intel()`, returning all three layers side by side. **Not fused** —
  that's Phase 5.
- `backend/app/schemas/analyze_schema.py` — `AnalyzeResponse` gained `threat_label: str`,
  `threat_score: int`, `threat_flags: List[str]`, additive to the unchanged Phase 2/3
  fields.
- `backend/app/db/models.py` — `Scan` table gained `threat_label` (String) and
  `threat_score` (Integer) columns, additive to the unchanged Phase 2/3 columns.
- `backend/requirements.txt` — added `requests==2.32.3`, `python-whois==0.9.4`,
  `python-dotenv==1.0.1`.
- `backend/.env` — real, gitignored config file (separate from `.env.example`, which
  stays as the untouched template). Contains the live `SAFE_BROWSING_API_KEY` and
  `DATABASE_URL`.
- `backend/thinkbeforeclick.db` — deleted and recreated during Phase 4 setup so SQLite
  would pick up the new `threat_label`/`threat_score` columns on the `scans` table (dev
  DB, no data loss of consequence).

## Verified working (Phase 4 tests passed)
- Message-only request (no URL) → `threat_label: "Not checked"`, `threat_score: 0`,
  `threat_flags: []` — correct, since there's no URL for threat-intel to check.
- Google's official Safe Browsing test URL
  (`http://testsafebrowsing.appspot.com/s/malware.html`) → `threat_label: "Flagged"`,
  `threat_score: 40`, flag: `"Google Safe Browsing flagged this URL (MALWARE)"`. WHOIS
  failed gracefully on this one (shared `appspot.com` subdomain, no own WHOIS record) —
  expected, did not crash the response.
- `https://www.google.com` → `threat_label: "Clean"`, `threat_score: 0`. WHOIS ran
  successfully and silently found no recent-registration flag (long-established domain)
  — confirms the WHOIS logic itself works correctly end-to-end when a domain has real
  WHOIS data.
- A nonexistent placeholder domain → WHOIS failed gracefully
  (`"WHOIS lookup failed — skipped (PywhoisError)"`), no crash, `threat_label: "Clean"`.
- `POST /analyze` with `{}` → still 422, validation unchanged from Phase 1.
- Hit and fixed one bug along the way: the Safe Browsing API key was initially saved
  into `backend/.env.example` (the template file) instead of `backend/.env` (the real,
  gitignored config file actually read by `config.py`), so every threat-intel call
  silently skipped the Safe Browsing check with `"Safe Browsing check skipped: no API
  key configured"` even though a key existed on disk. Fixed by regenerating a fresh API
  key (the original was treated as exposed since it had been visible in a shared
  screenshot) and saving it into `backend/.env` instead. Confirmed working after the
  fix — the Safe Browsing test URL correctly returned `"Flagged"` with a populated
  threat type.

## Confirmed decisions (do not re-litigate these)
- Project name: **ThinkBeforeClick**
- No user accounts or login — fully anonymous, stateless
- "Report this message" feeds anonymized data into future ML retraining
- Extension model: Tier 1 passive local-rules-only scanning (always on, no API calls) +
  Tier 2 active popup deep-check (full pipeline via backend API)
- Detection pipeline: rule-based layer + ML/NLP layer (TF-IDF + Logistic Regression) +
  threat-intel layer (Google Safe Browsing + WHOIS), combined by a fusion engine
- Build order: **Backend API → Web App (deployed to Render) → Browser Extension**
- We move phase by phase, testing each phase before starting the next
- Backend framework: **FastAPI** (not Flask)
- Database: **SQLite**, tables for `scans` and `reports`
- Single venv at project root, not per-folder
- Phase 2 rule-based Safe/Suspicious/High Risk thresholds (score >= 40 → High Risk,
  >= 15 → Suspicious, else Safe) are still a placeholder, untouched — the real
  weighting/labeling logic is redesigned by the fusion engine in Phase 5
- ML classifier: TF-IDF (unigrams+bigrams) + Logistic Regression, `class_weight="balanced"`,
  0.5 probability threshold for Safe/Phishing — trained to favor recall over precision.
  These Phase 3 choices are settled; don't re-litigate or "upgrade" the model type
- Threat-intel: Google Safe Browsing API v4 (the current, non-legacy API — not the
  deprecated v3/"(Legacy)" version), threat score 40 for any match across MALWARE /
  SOCIAL_ENGINEERING / UNWANTED_SOFTWARE / POTENTIALLY_HARMFUL_APPLICATION; WHOIS via
  `python-whois`, "new domain" threshold set at under 180 days old, score 20. These
  scoring values are Phase 4 placeholders like the rule/ML layers — real weighting is
  Phase 5's job, don't tune them now
- Rule, ML, and threat-intel layers are returned **side by side, unfused**, in
  `/analyze` — this is intentional per phases.md, not an oversight to "fix" before Phase 5
- `.env.example` stays as the untouched template in the repo; the real, gitignored
  `.env` is where actual secrets (API keys) live — don't conflate the two again

## Target file structure
See `phases.md` for the complete folder tree (backend/, webapp/, extension/, docs/).

## Next step
**Phase 5 — Fusion Engine.**
- 5.1 Design the weighting logic (how much each layer — rule, ML, threat-intel —
  contributes to the final score)
- 5.2 Build the risk classification (Safe / Suspicious / High Risk) on the combined score
- 5.3 Build the explanation generator — shows which layer(s) triggered and why
- 5.4 Build the recommendation generator based on final risk level
- 5.5 Full pipeline test: message + URL in → complete explainable result out

## Notes for continuing this project in a new chat
- Do not re-ask about accounts, hosting choice, ML approach, build order, venv setup, or
  Safe Browsing API version — all decided above
- Do not revert to Flask or reintroduce the hackathon's keyword-only logic
- Do not tune/redesign the Phase 2 rule-based score thresholds, the Phase 3 ML approach,
  or the Phase 4 threat-intel scoring values in isolation — all of that is explicitly
  Phase 5 fusion engine work
- Do not build the web app or extension code yet — Phase 5 (fusion engine) only
- Confirm which phase we're on before generating code
