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
- 3.1 Source and combine public datasets, clean and label consistently
- 3.2 Feature extraction with TF-IDF — unigrams + bigrams
- 3.3 Train a Logistic Regression classifier — `class_weight="balanced"`, `C=1.0`
- 3.4 Evaluate — precision, recall, F1 (optimized for recall, per project goal)
- 3.5 Save the trained model (`joblib`), wrap it as a callable service function
- 3.6 Integrate into the pipeline alongside the rules layer — `ml_engine.py`

> scikit-learn pinned to **1.7.2** — do not upgrade without re-testing the full
> dependency chain (an attempt at 1.8.0 broke compatibility with other dependencies).

### PHASE 4 — Threat-Intelligence Layer ✅ COMPLETE
**Goal:** real external verification for URLs.
- 4.1 Google Safe Browsing API key + integration — `check_safe_browsing()`
- 4.2 WHOIS domain-age lookup (`python-whois`) — `check_domain_age()`, "new domain"
  threshold under 180 days
- 4.3 Handle API failures/timeouts gracefully (never let an external outage break the tool)
- 4.4 Integrate results into the pipeline as the third signal — `run_threat_intel()`

### PHASE 5 — Fusion Engine ✅ COMPLETE
**Goal:** combine all three layers into one trustworthy, explainable result.
- 5.1 Weighting: rule 30% / ML 40% / threat-intel 30% when a URL is present; dynamic
  reweighting when no URL is given
- 5.2 Thresholds: `>= 70` High Risk, `>= 35` Suspicious, else Safe — plus one override: a
  confirmed Google Safe Browsing match forces High Risk with a score floor of 90
- 5.3 Explanation generator — top 4 flags, threat-intel > ML > rule priority
- 5.4 Recommendation generator — canned bullet list (`List[str]`) keyed off final label
- 5.5 Full pipeline tested — 11 documented test cases against the real `/analyze` endpoint

### PHASE 6 — Web App Frontend ✅ COMPLETE
**Goal:** a clean interface calling the real API.
- 6.1 Analyzer page: matrix-rain intro (4s glitch) -> terminal-panel input dialog
  (persistent, no timeout) -> processing state -> themed verdict card (High Risk /
  Suspicious / Safe), wired to the real `/analyze` response shape
- 6.2 "Report this message" / `how-it-works.html` — **dropped from scope by product
  decision**, not built
- 6.3 Responsive layout, self-hosted GSAP for animation (CDN version caused a silent
  animation-breaking bug in testing — do not switch back)
- 6.4 Connected to backend, full local end-to-end test confirmed working

### PHASE 7 — Deployment ✅ COMPLETE
**Goal:** it's live on the internet.
- 7.1 Trained ML model files (`classifier.joblib`, `vectorizer.joblib`) committed to
  GitHub (small file size made this simpler than Release-asset downloads); dataset CSV
  stays gitignored, training-only
- 7.2 Backend deployed to Render (Web Service), Root Directory `backend`, own
  `requirements.txt` copy inside `backend/`, `SAFE_BROWSING_API_KEY` set as a Render
  environment variable — live and verified at `https://thinkbeforeclick.onrender.com`
- 7.3 Frontend deployed to Render (Static Site), `API_BASE` in `analyzer.js` updated to
  the live backend URL — live at a custom domain, `https://thinkbeforeclick.me`
- 7.4 CORS locked down from wildcard to an explicit allowlist including the deployed
  frontend/custom domain
- 7.5 Live end-to-end test: 5 documented cases re-run against the live stack (not
  localhost) and confirmed correct

> Known limitation: SQLite on Render's free tier lives on ephemeral disk — `scans`/
> `reports` tables reset on redeploys/restarts. Acceptable since scan history isn't a
> product requirement (no accounts, fully anonymous by design).

### PHASE 8 — Browser Extension: Passive Layer (Tier 1) — NOT STARTED
**Goal:** always-on background scanning.
- 8.1 Manifest V3 setup, permissions scoped to target sites (Gmail, Outlook Web, WhatsApp Web)
- 8.2 Content script: extract visible text + links from the page
- 8.3 Run local rule-based check only (no API call) inside the content script
- 8.4 Inline warning UI on flagged content + badge count on the extension icon

### PHASE 9 — Browser Extension: Active Layer (Tier 2) — NOT STARTED
**Goal:** on-demand full analysis from the extension.
- 9.1 Popup UI — same analyzer layout as the web app
- 9.2 Right-click context menu: "Scan with ThinkBeforeClick" on selected text/links
- 9.3 Popup and context menu both call the deployed backend's `/analyze` endpoint
- 9.4 Report button wired the same way as the web app
- 9.5 Package for Chrome; note Firefox manifest differences if targeting both

---

## Current status summary
**Live and working:** Phases 1-7 (backend, ML, threat-intel, fusion engine, frontend,
deployment). Publicly reachable at `https://thinkbeforeclick.me` (frontend) and
`https://thinkbeforeclick.onrender.com` (backend API).

**Not yet started:** Phases 8-9 (Browser Extension).

**Also open (not a phase, ongoing side-track):** an ML model retrain is in progress — a
combined ~106k-row dataset (original 59k + CEAS + filtered/deduped KD synthetic data,
English-only) has been prepared and handed off; retrain + evaluation + redeploy of the
new `.joblib` files not yet confirmed complete as of this update.

## Project folder structure (as actually deployed)
```
thinkbeforeclick/
|
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint, CORS locked to deployed domains
│   │   ├── api/                       # health.py, analyze.py, report.py (stub)
│   │   ├── schemas/                   # analyze_schema.py
│   │   ├── services/                  # rule_engine.py, ml_engine.py, threat_intel.py,
│   │   │                              #   fusion_engine.py
│   │   ├── ml/
│   │   │   ├── train_model.py
│   │   │   ├── dataset/               # gitignored - phishing_dataset.csv, local only
│   │   │   └── model/                 # TRACKED in git - classifier.joblib, vectorizer.joblib
│   │   ├── db/                        # database.py, models.py
│   │   └── core/                      # config.py, logging.py
│   ├── requirements.txt               # duplicated at repo root AND here for Render
│   └── .env                           # gitignored - real SAFE_BROWSING_API_KEY, local only
|
├── webapp/                            # deployed as a Render Static Site
│   ├── index.html
│   ├── static/{css,js}/
│   └── static/js/vendor/gsap.min.js   # self-hosted, not CDN
|
├── extension/                         # Phase 8-9, not built yet
|
├── docs/
│   ├── PROJECT_STATE.md
│   ├── phases.md                      # this file
│   └── AI_Shield_Project_Blueprint.md
|
└── README.md
```
