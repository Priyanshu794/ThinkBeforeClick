### PHASE 1 — Backend Foundation ✅ COMPLETE
**Goal:** a working, empty-but-real API skeleton, nothing clever yet.
- 1.1 Project structure: `app/`, `app/api/`, `app/services/`, `app/models/`, `app/db/`
- 1.2 FastAPI app initialized, `/health` endpoint, auto docs working (`/docs`)
- 1.3 `/analyze` endpoint scaffolded — accepts `message` + `url`, validates input
  (Pydantic schema), returns a placeholder response
- 1.4 SQLite database set up — tables for `scans` and `reports`
- 1.5 Test the skeleton end-to-end with a dummy request (Postman/curl or `/docs`)

### PHASE 2 — Rule-Based Detection Layer (upgraded) ✅ COMPLETE
**Goal:** the smartest possible version of "keyword matching," done properly.
- 2.1 Rebuild message rules: regex patterns instead of plain substring checks, handling
  obfuscation (e.g. "u.r.g.e.n.t", spaced-out words, symbol substitution)
- 2.2 Rebuild URL rules: HTTPS check, shortener detection, suspicious TLDs, hyphen/keyword
  heuristics — same categories as before, more robust matching
- 2.3 Wire both into the real `/analyze` endpoint (replacing the placeholder)
- 2.4 Test against a set of known phishing + safe sample messages

### PHASE 3 — ML/NLP Layer ✅ COMPLETE
**Goal:** a real trained classifier plugged into the pipeline.
- 3.1 Source and combine public datasets (SMS Spam Collection + a phishing email dataset),
  clean and label consistently — done: `phishing_dataset.csv`, 59,206 rows, `text`/`label`
  columns, ~60/40 safe/phishing split
- 3.2 Feature extraction with TF-IDF — unigrams + bigrams, `min_df=3`, `max_df=0.9`,
  `max_features=50000`
- 3.3 Train a Logistic Regression classifier — `class_weight="balanced"`, `C=1.0`
- 3.4 Evaluate — precision, recall, F1 (optimized for recall, per project goal)
- 3.5 Save the trained model (`joblib`), wrap it as a callable service function —
  `classifier.joblib` + `vectorizer.joblib`, verified working with real predictions
  (obvious phishing → 92–96% confidence, casual/safe messages → 2–6% confidence)
- 3.6 Integrate into the pipeline alongside the rules layer — `ml_engine.py`

> **Note:** the trained model/vectorizer files and the dataset CSV are gitignored and
> intentionally NOT pushed to GitHub — they exist only on the developer's local machine.
> A fresh clone (new environment, new deploy target, new chat's sandbox) will need these
> files re-provided to actually exercise this layer; without them `ml_engine.py` degrades
> gracefully to `ml_label: "Unknown"` instead of crashing.
>
> **scikit-learn is pinned to 1.7.2** in `requirements.txt` — the model was trained and
> must be loaded on this exact version. An attempt to move to 1.8.0 broke compatibility
> with other dependencies (uvicorn, etc.). Do not upgrade without re-testing the full
> dependency chain.

### PHASE 4 — Threat-Intelligence Layer ✅ COMPLETE
**Goal:** real external verification for URLs.
- 4.1 Get a free Google Safe Browsing API key, integrate the lookup — `check_safe_browsing()`,
  Safe Browsing API v4, real key required in a local, gitignored `.env` (`.env.example` is
  the untouched template in the repo)
- 4.2 Add WHOIS domain-age lookup (`python-whois`) — `check_domain_age()`, "new domain"
  threshold under 180 days
- 4.3 Handle API failures/timeouts gracefully (never let an external outage break the tool)
  — confirmed: WHOIS failures (`PywhoisError`, timeouts) are caught and skipped with a
  flag, never crash `/analyze`
- 4.4 Integrate results into the pipeline as the third signal — `run_threat_intel()`

### PHASE 5 — Fusion Engine ✅ COMPLETE (re-verified and corrected)
**Goal:** combine all three layers into one trustworthy, explainable result.
- 5.1 Design the weighting logic — **final:** rule 30% / ML 40% / threat-intel 30% when a
  URL is present. When no URL is submitted (`threat_label == "Not checked"`), threat-intel's
  30% is redistributed proportionally across rule/ML, keeping their 30:40 ratio (~42.86% /
  ~57.14%). Each layer's raw score is normalized to 0–100 first (rule capped at 100, ML
  already 0–100, threat-intel capped at **60** — the real max possible raw score, Safe
  Browsing 40 + WHOIS 20)
- 5.2 Build the risk classification on the combined score — **final thresholds:**
  `>= 70` → High Risk, `>= 35` → Suspicious, else Safe. Plus **one** override: a confirmed
  Google Safe Browsing match forces High Risk with a score floor of 90, regardless of the
  blended score, since it's independently-verified external ground truth rather than a
  probabilistic guess. There is intentionally no second override (an earlier "rule+ML
  agreement" override was considered and deliberately dropped — the current design is a
  plain weighted average plus only the one Safe Browsing override)
- 5.3 Build the explanation generator — pools flags from whichever layers fired, ordered
  threat-intel first (external ground truth), then ML, then rule; capped at 4 total lines
  (override note counts toward the cap if it fires); empty list if final label is Safe
  (matches the Safe UI design: just a checkmark, no bullet list)
- 5.4 Build the recommendation generator — a short canned bullet list (`List[str]`, not a
  single string) keyed only off the final label: 3 bullets for High Risk, 3 for Suspicious,
  empty list for Safe
- 5.5 Full pipeline test: message + URL in → complete explainable result out — **11 test
  cases run against the real `/analyze` endpoint**, covering safe/suspicious/high-risk,
  message-only/URL-only/combined, and edge cases (empty body, whitespace-only message).
  One real bug was found and fixed during this testing: a confirmed-malicious test URL
  (Google's own Safe Browsing test URL) was incorrectly landing as "Safe" due to (a) a
  threat-intel normalization cap bug (was 100, should be 60) and (b) no override existing
  yet to weight a confirmed external match heavily enough. Both fixed and re-verified with
  no regressions to any other test case.

> **Do not re-tune the weights, thresholds, or the single override without a new, specific
> failing test case driving it** — the current values were arrived at through real testing,
> not arbitrary choice, and are documented with their test cases in `PROJECT_STATE.md`.

### PHASE 6 — Web App Frontend (next up — not started)
**Goal:** a clean, deployable interface calling the real API.
- 6.1 Analyzer page: message + URL input, results panel (score, per-layer breakdown, flags,
  recommendation) — **full visual design already confirmed** (see `PROJECT_STATE.md`
  "Frontend plan" section): matrix-rain intro with 4-second glitch effect → skull reveal →
  2-second mouth-opening animation revealing a persistent (non-timing-out) input dialog →
  processing state on submit → verdict card with three visual themes (High Risk / Suspicious
  / Safe) driven by `final_risk_label`
- 6.2 "Report this message" flow wired to the `/report` endpoint (`/report` is still an
  empty stub — this is new backend work too, not just frontend)
- 6.3 "How it works" page explaining the 3-layer pipeline + fusion engine in plain language
- 6.4 Responsive/mobile-friendly layout
- 6.5 Connect frontend to backend, full local end-to-end test — response shape to build
  against: `final_risk_label: str`, `final_risk_score: int`, `explanation: List[str]`,
  `recommendation: List[str]`

### PHASE 7 — Deployment
**Goal:** it's live on the internet.
- 7.1 Push repo to GitHub
- 7.2 Deploy backend + database to Render (or similar free-tier host)
- 7.3 Deploy/serve frontend (same host or static hosting)
- 7.4 Environment variables for API keys, CORS setup between frontend/backend
- 7.5 Live end-to-end test with real sample messages from a real URL

### PHASE 8 — Browser Extension: Passive Layer (Tier 1)
**Goal:** always-on background scanning.
- 8.1 Manifest V3 setup, permissions scoped to target sites (Gmail, Outlook Web, WhatsApp Web)
- 8.2 Content script: extract visible text + links from the page
- 8.3 Run local rule-based check only (no API call) inside the content script
- 8.4 Inline warning UI on flagged content + badge count on the extension icon

### PHASE 9 — Browser Extension: Active Layer (Tier 2)
**Goal:** on-demand full analysis from the extension.
- 9.1 Popup UI — same analyzer layout as the web app
- 9.2 Right-click context menu: "Scan with ThinkBeforeClick" on selected text/links
- 9.3 Popup and context menu both call the deployed backend's `/analyze` endpoint
- 9.4 Report button wired the same way as the web app
- 9.5 Package for Chrome; note Firefox manifest differences if targeting both

---
thinkbeforeclick/
│
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app entrypoint
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── analyze.py             # /analyze route
│   │   │   ├── report.py              # /report route
│   │   │   └── health.py              # /health route
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── analyze_schema.py      # Pydantic request/response models
│   │   │                              #   recommendation is List[str], not str
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── rule_engine.py         # Phase 2 — regex/keyword layer
│   │   │   ├── ml_engine.py           # Phase 3 — ML classifier wrapper
│   │   │   ├── threat_intel.py        # Phase 4 — Safe Browsing + WHOIS
│   │   │   └── fusion_engine.py       # Phase 5 — combines all layers (final design)
│   │   │
│   │   ├── ml/
│   │   │   ├── train_model.py         # training script (Phase 3)
│   │   │   ├── dataset/               # gitignored — cleaned public dataset, local only
│   │   │   └── model/                 # gitignored — trained artifacts, local only
│   │   │       ├── classifier.joblib
│   │   │       └── vectorizer.joblib
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py            # DB connection/session
│   │   │   └── models.py              # SQLite tables: scans, reports
│   │   │
│   │   └── core/
│   │       ├── config.py              # settings, env vars, API keys
│   │       └── logging.py
│   │
│   ├── requirements.txt                # scikit-learn pinned to 1.7.2 — do not upgrade
│   ├── .env                           # API keys (Safe Browsing, etc.) — gitignored
│   ├── .env.example                   # untouched template, safe to commit
│   └── thinkbeforeclick.db            # SQLite file (Phase 1)
│
├── webapp/
│   ├── index.html                     # analyzer page
│   ├── how-it-works.html
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── analyzer.js            # calls /analyze
│   │       └── report.js              # calls /report
│   └── assets/
│       └── icons/
│
├── extension/
│   ├── manifest.json                  # Manifest V3 config
│   ├── background.js                  # service worker (badge, context menu)
│   ├── content-script.js              # Phase 8 — passive Tier 1 scanner
│   ├── popup/
│   │   ├── popup.html                 # Phase 9 — Tier 2 deep-check UI
│   │   ├── popup.css
│   │   └── popup.js
│   └── icons/
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
│
├── docs/
│   ├── PROJECT_STATE.md               # detailed, current, test-verified project state
│   └── AI_Shield_Project_Blueprint.md # this planning doc
│
└── README.md

### 4.3 Data Flow Summary
- No accounts, no personal data stored.
- Only reported message/URL content is retained, anonymously, for ML retraining.
- Passive extension scanning never leaves the browser (local rules only).
- Active/deep checks send content to the backend for the full pipeline, and it's discarded
  after the response unless the user explicitly reports it.

---

## 5. Confirmed Decisions

- Project name: **ThinkBeforeClick**
- No user accounts or login — fully anonymous, stateless
- Reported messages auto-feed into future ML model retraining
- Extension: hybrid passive (always-on local scanning) + active (on-demand deep popup check)
- Full rebuild from scratch — no code carried over from the earlier hackathon prototype
- Build order: **Backend API → Web App (deployed) → Browser Extension**
- We proceed **phase by phase**, testing each phase before moving to the next
- Fusion engine weighting/thresholds/override are finalized against real test cases (Phase
  5) — see `PROJECT_STATE.md` for the full verified test suite before re-tuning anything