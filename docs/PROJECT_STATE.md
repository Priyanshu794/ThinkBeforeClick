# ThinkBeforeClick — Project State

_Last updated: end of Phase 2, confirmed working._

## Where we are
Phase 1 (Backend Foundation) and Phase 2 (Rule-Based Detection Layer) are both complete
and verified working. Ready to begin Phase 3 (ML/NLP Layer).

## What exists right now
- Full folder structure created (backend/, webapp/, extension/, docs/) per phases.md
- `backend/app/main.py` — FastAPI app entrypoint, includes health + analyze routers,
  creates DB tables on startup
- `backend/app/api/health.py` — `GET /health` → `{"status": "ok"}`
- `backend/app/api/analyze.py` — `POST /analyze` — validates input, runs the rule engine,
  writes a scan row (with real rule-based label/score) to the `scans` table, returns
  `risk_label`, `risk_score`, and `flags`
- `backend/app/schemas/analyze_schema.py` — `AnalyzeRequest` (message/url, at least one
  required) and `AnalyzeResponse` (now includes `flags: List[str]`) Pydantic models
- `backend/app/services/rule_engine.py` — Phase 2 core logic:
  - `analyze_message()` — regex-based keyword matching with obfuscation handling
    (dots/dashes/underscores/spaces between letters), excessive punctuation/caps
    detection, sensitive-info request detection
  - `analyze_url()` — HTTPS check, known-shortener detection, suspicious TLD detection,
    hyphen-heavy domain check, suspicious keyword check, raw-IP check, excessive
    subdomain check
  - `run_rule_engine()` — combines message + URL scores into `rule_score`, `rule_label`
    (Safe / Suspicious / High Risk via threshold, will be superseded by fusion engine in
    Phase 5), and `rule_flags`
- `backend/app/db/database.py` — SQLAlchemy engine/session setup, SQLite at
  `backend/thinkbeforeclick.db`
- `backend/app/db/models.py` — `Scan` and `Report` table models (Report table defined,
  not yet used by any endpoint)
- `backend/requirements.txt` — fastapi, uvicorn, sqlalchemy, pydantic, python-multipart
- `backend/app/api/report.py`, `app/services/ml_engine.py`, `app/services/threat_intel.py`,
  `app/services/fusion_engine.py`, `app/ml/*`, `app/core/*` — still empty, reserved for
  later phases (do not build these yet)
- Virtual environment: single `venv/` at project root (not inside backend/) — always
  activate this before running anything

## Verified working (Phase 1 + Phase 2 tests passed)
- `uvicorn app.main:app --reload` starts cleanly from `backend/`, no errors
- `/docs` (Swagger UI) loads, lists `GET /health` and `POST /analyze`
- `GET /health` → 200, `{"status": "ok"}`
- `POST /analyze` with a known-phishing sample (obfuscated "u.r.g.e.n.t", shortener URL,
  no HTTPS, excessive punctuation/caps) → 200, `risk_label: "High Risk"`, `risk_score: 105`,
  `flags` populated with multiple specific reasons
- `POST /analyze` with a known-safe sample (plain message, HTTPS Wikipedia URL) → 200,
  `risk_label: "Safe"`, `risk_score: 0`, `flags: []`
- `POST /analyze` with `{}` → 422, correct validation error message
- `thinkbeforeclick.db` created automatically in `backend/`

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
- Current rule-based Safe/Suspicious/High Risk thresholds (score >= 40 → High Risk,
  >= 15 → Suspicious, else Safe) are a Phase 2 placeholder — the real weighting/labeling
  logic will be redesigned by the fusion engine in Phase 5, so don't "fix" or tune these
  thresholds now

## Target file structure
See `phases.md` for the complete folder tree (backend/, webapp/, extension/, docs/).

## Next step
**Phase 3 — ML/NLP Layer.**
- 3.1 Source and combine public datasets (SMS Spam Collection + a phishing email dataset),
  clean and label consistently
- 3.2 Feature extraction with TF-IDF
- 3.3 Train a Logistic Regression (or Naive Bayes) classifier
- 3.4 Evaluate — precision, recall, F1 (optimize for recall: missing real phishing is worse
  than a false alarm)
- 3.5 Save the trained model (`joblib`), wrap it as a callable service function in
  `backend/app/services/ml_engine.py`
- 3.6 Integrate into the pipeline alongside the rules layer (both scores/flags returned
  from `/analyze`, but do NOT build the fusion engine yet — that's Phase 5)

## Notes for continuing this project in a new chat
- Do not re-ask about accounts, hosting choice, ML approach, build order, or venv setup —
  all decided above
- Do not revert to Flask or reintroduce the hackathon's keyword-only logic
- Do not tune/redesign the Phase 2 rule-based score thresholds — that's fusion engine work
  (Phase 5)
- Do not build threat-intel, fusion, web app, or extension code yet — Phase 3 (ML/NLP) only
- Confirm which phase we're on before generating code