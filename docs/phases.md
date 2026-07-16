
### PHASE 1 — Backend Foundation
**Goal:** a working, empty-but-real API skeleton, nothing clever yet.
- 1.1 Project structure: `app/`, `app/api/`, `app/services/`, `app/models/`, `app/db/`
- 1.2 FastAPI app initialized, `/health` endpoint, auto docs working (`/docs`)
- 1.3 `/analyze` endpoint scaffolded — accepts `message` + `url`, validates input
  (Pydantic schema), returns a placeholder response
- 1.4 SQLite database set up — tables for `scans` and `reports`
- 1.5 Test the skeleton end-to-end with a dummy request (Postman/curl or `/docs`)

### PHASE 2 — Rule-Based Detection Layer (upgraded)
**Goal:** the smartest possible version of "keyword matching," done properly.
- 2.1 Rebuild message rules: regex patterns instead of plain substring checks, handling
  obfuscation (e.g. "u.r.g.e.n.t", spaced-out words, symbol substitution)
- 2.2 Rebuild URL rules: HTTPS check, shortener detection, suspicious TLDs, hyphen/keyword
  heuristics — same categories as before, more robust matching
- 2.3 Wire both into the real `/analyze` endpoint (replacing the placeholder)
- 2.4 Test against a set of known phishing + safe sample messages

### PHASE 3 — ML/NLP Layer
**Goal:** a real trained classifier plugged into the pipeline.
- 3.1 Source and combine public datasets (SMS Spam Collection + a phishing email dataset),
  clean and label consistently
- 3.2 Feature extraction with TF-IDF
- 3.3 Train a Logistic Regression (or Naive Bayes) classifier
- 3.4 Evaluate — precision, recall, F1 (optimize for recall: missing real phishing is worse
  than a false alarm)
- 3.5 Save the trained model (`joblib`), wrap it as a callable service function
- 3.6 Integrate into the pipeline alongside the rules layer

### PHASE 4 — Threat-Intelligence Layer
**Goal:** real external verification for URLs.
- 4.1 Get a free Google Safe Browsing API key, integrate the lookup
- 4.2 Add WHOIS domain-age lookup (`python-whois`)
- 4.3 Handle API failures/timeouts gracefully (never let an external outage break the tool)
- 4.4 Integrate results into the pipeline as the third signal

### PHASE 5 — Fusion Engine
**Goal:** combine all three layers into one trustworthy, explainable result.
- 5.1 Design the weighting logic (how much each layer contributes to the final score)
- 5.2 Build the risk classification (Safe / Suspicious / High Risk) on the combined score
- 5.3 Build the explanation generator — shows which layer(s) triggered and why
- 5.4 Build the recommendation generator based on final risk level
- 5.5 Full pipeline test: message + URL in → complete explainable result out

### PHASE 6 — Web App Frontend
**Goal:** a clean, deployable interface calling the real API.
- 6.1 Analyzer page: message + URL input, results panel (score, per-layer breakdown, flags,
  recommendation)
- 6.2 "Report this message" flow wired to the `/report` endpoint
- 6.3 "How it works" page explaining the 3-layer pipeline in plain language
- 6.4 Responsive/mobile-friendly layout
- 6.5 Connect frontend to backend, full local end-to-end test

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
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── rule_engine.py         # Phase 2 — regex/keyword layer
│   │   │   ├── ml_engine.py           # Phase 3 — ML classifier wrapper
│   │   │   ├── threat_intel.py        # Phase 4 — Safe Browsing + WHOIS
│   │   │   └── fusion_engine.py       # Phase 5 — combines all layers
│   │   │
│   │   ├── ml/
│   │   │   ├── train_model.py         # training script (Phase 3)
│   │   │   ├── dataset/               # cleaned public datasets
│   │   │   └── model/
│   │   │       └── classifier.joblib  # saved trained model
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
│   ├── requirements.txt
│   ├── .env                           # API keys (Safe Browsing, etc.) — gitignored
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
│   └── ThinkBeforeClick_Blueprint.md   # this planning doc
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
