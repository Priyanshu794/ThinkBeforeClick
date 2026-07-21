# ThinkBeforeClick — Project State

_Last updated: end of Phase 7 (Deployment), live on Render, full end-to-end test confirmed
working against the real deployed stack (not just local)._

## Where we are
Phases 1–6 (backend: rule engine, ML classifier, threat-intel, fusion engine; frontend:
matrix-rain analyzer flow) remain complete and verified — unchanged this session.
**Phase 7 (Deployment) is now done: both backend and frontend are live on Render, CORS is
locked down, and 5 end-to-end test cases were re-run against the live URLs (not localhost)
and confirmed correct.**

## Live URLs
- **Backend API:** `https://thinkbeforeclick.onrender.com`
  - `/health` → `{"status": "ok"}`
  - `/docs` → Swagger UI, working
  - `/analyze` → verified returning correct `ml_label`, `threat_label`, `final_risk_label`
    against real requests (see "Deployment verification" below)
- **Frontend:** `https://thinkbeforeclick-frontend.onrender.com`
  - Full matrix-rain → terminal dialog → verdict card flow confirmed working live
- **GitHub repo:** `https://github.com/Priyanshu794/ThinkBeforeClick` (`main` branch)
- **Render project:** "ThinkBeforeClick" under Render account, two services:
  - Web Service: `ThinkBeforeClick` (backend), Service ID `srv-d9f3du37uimc73ajp11g`
  - Static Site: frontend (webapp)

## What changed this session — deployment-specific fixes

1. **`.gitignore` updated to track the trained model files.** Originally
   `backend/app/ml/model/*` blanket-ignored the whole folder (dataset AND model). Changed
   to:
   ```
   backend/app/ml/model/*
   !backend/app/ml/model/.gitkeep
   !backend/app/ml/model/*.joblib
   ```
   The 70MB `phishing_dataset.csv` **stays gitignored** (training-only, never needed at
   runtime). `classifier.joblib` and `vectorizer.joblib` **are now committed and pushed to
   GitHub** — confirmed present in the repo. This was the correct call given their small
   file size; no need for Release-asset downloads or build-script fetching.

2. **`requirements.txt` duplicated inside `backend/`.** The original file lived only at
   repo root, but Render's Root Directory setting (`backend`) meant the build command
   `pip install -r requirements.txt` couldn't find it. Fixed by adding a copy at
   `backend/requirements.txt`. **Two copies now exist** (root + `backend/`) — if a new
   Python dependency is ever added, update **both** files, or consolidate to just the
   `backend/` copy later (not urgent).

3. **`analyzer.js`'s `API_BASE` updated** from `http://127.0.0.1:8000` to
   `https://thinkbeforeclick.onrender.com` — required once the frontend went public and
   could no longer reach localhost.

4. **CORS tightened in `backend/app/main.py`.** Changed from `allow_origins=["*"]` to an
   explicit allowlist:
   ```python
   allow_origins=[
       "https://thinkbeforeclick-frontend.onrender.com",
       "http://127.0.0.1:5500",
       "http://localhost:5500",
   ]
   ```
   Confirmed working — no CORS errors in browser console, full flow still works live.

## Render configuration (for reference / redeploying from scratch)

**Backend (Web Service):**
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables set: `PYTHON_VERSION` (matches local dev version),
  `SAFE_BROWSING_API_KEY` (real key, set directly in Render dashboard — never in a
  committed file)
- Instance type: Free tier — **note: free tier spins down after inactivity, first request
  after idle can take ~50+ seconds.** Known/expected behavior, not a bug.

**Frontend (Static Site):**
- Root Directory: `webapp`
- Build Command: (none — plain HTML/CSS/JS needs no build step)
- Publish Directory: `.`

## Deployment verification — actually tested against the live stack

Confirmed via direct testing against the **live** URLs (not localhost) this session:

1. `/health` → `{"status":"ok"}` ✅
2. `/docs` Swagger UI loads correctly ✅
3. `/analyze` with an obvious phishing message (no URL) → real live response:
   `ml_label: "Phishing"` (98.55% confidence), `threat_label: "Not checked"`,
   `final_risk_label: "High Risk"`, `final_risk_score: 86` — confirms the committed
   `.joblib` files loaded correctly on Render (not degraded to "Unknown"), and confirms
   the no-URL reweighting logic is intact in production. ✅
4. Full frontend flow (intro → terminal dialog → THINK → verdict card) re-run live and
   confirmed rendering correctly. ✅
5. **5 end-to-end cases re-tested through the live frontend UI** (not Swagger) and all
   confirmed correct:
   - Casual safe message, no URL → Safe, no bullet lists ✅
   - Obvious phishing message, no URL → High Risk ✅
   - Clean URL only (wikipedia.org) → Safe ✅
   - Suspicious-structured URL only → Safe/Suspicious (matches documented Case 5
     behavior — expected, not a bug) ✅
   - Phishing message + URL combined → High Risk ✅
6. CORS lockdown verified — no browser console errors, full flow still works after
   restricting `allow_origins` away from wildcard. ✅

**Net result: Phase 7 fully complete. The live, public app behaves identically to the
locally-tested version — no regressions introduced by the deployment process itself.**

## Confirmed decisions (carried over, still valid)
- Project name: **ThinkBeforeClick**; no accounts/login; fully anonymous, stateless
- Backend: FastAPI, SQLite (⚠️ **new note:** on Render's free tier, SQLite lives on
  ephemeral disk — `scans`/`reports` tables reset on redeploys/restarts; acceptable for
  this project since scan history isn't a product requirement)
- Detection pipeline: rule-based + ML/NLP + threat-intel, combined by the fusion engine —
  unchanged, still rule 30% / ML 40% / threat-intel 30%, one Safe Browsing override,
  thresholds ≥70 High Risk / ≥35 Suspicious — **do not re-tune without deciding first**
  whether the two open detection gaps below (Cases 3 & 4) warrant it
- ML model/vectorizer files are **now committed to GitHub** (small file size made this the
  right call) — the 70MB dataset CSV remains gitignored, training-only
- scikit-learn pinned to 1.7.2 — confirmed still working correctly on Render — do not
  upgrade without re-testing the full dependency chain
- Build order: Backend API → Web App → Browser Extension → **Deployment (done)**
- `how-it-works.html` and `report.js` remain out of scope (dropped by product decision in
  the Phase 6 session) — do not build unless asked again
- GitHub repo: `https://github.com/Priyanshu794/ThinkBeforeClick`, `main` branch — the
  project connector still does not auto-sync; use "Sync now" or clone directly for a fresh
  chat's view

## Not yet done
- Phase 8–9 — Browser Extension — not started (comes after deployment per build order,
  which is now satisfied)
- Backend detection gaps 3 & 4 from the Phase 6 session (documented below, unchanged) —
  need a larger threshold/override or ML-retraining conversation before touching anything
- Consolidating the duplicate `requirements.txt` (root + `backend/`) into one — cosmetic,
  not urgent
- Considering a paid Render tier if the free-tier spin-down (~50s cold start) becomes a
  real usability problem for actual users

## Known backend detection gaps — carried over from Phase 6, still open
3. **Bank OTP phishing, message-only** → came back **Suspicious** (score 65), not
   **High Risk**. Near-miss under the 70 threshold, not a keyword-coverage gap. Needs a
   threshold/weighting conversation or a narrow new override — deferred, bigger discussion.
4. **Subtly-worded scam, no urgency/shouting** → came back **Safe** (score 32). No rule
   keywords match; ML alone doesn't rate calm phrasing as phishing-like. Needs ML training
   dataset additions + a retrain — deferred, bigger scope than a quick fix.

(Cases 1 and 2 from the Phase 6 session — delivery/courier scam pattern and fake
exam-results/portal-login scam — were already resolved via `rule_engine.py` keyword/TLD
additions, unchanged and still correct this session.)

## Notes for continuing this project in a new chat
- Do not re-ask about hosting choice, deployment platform, CORS approach, or how the model
  files reached GitHub — all decided and verified above
- Do not move the `.joblib` files back to gitignored status — they need to stay tracked
  for Render deploys to have a working ML layer
- Do not revert CORS back to `allow_origins=["*"]` in production
- Do not attempt Phase 8 (browser extension) without first deciding whether to tackle the
  two open backend detection gaps (Cases 3 & 4) — ask which one to prioritize before
  writing code for either
- Confirm which phase/task we're on before generating code