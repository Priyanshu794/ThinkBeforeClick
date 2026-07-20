# ThinkBeforeClick — Project State

_Last updated: end of Phase 5, re-verified and corrected against actual GitHub code._

## Where we are
Phase 1 (Backend Foundation), Phase 2 (Rule-Based Detection Layer), Phase 3 (ML/NLP
Layer), Phase 4 (Threat-Intelligence Layer), and Phase 5 (Fusion Engine) are all complete
and **actually verified working** — tested end-to-end against the real cloned GitHub repo,
not just claimed. Ready to begin Phase 6 (Web App Frontend).

**Important process note for whoever continues this project:** earlier in this project's
history, this file claimed Phase 5 was complete with a specific fusion design (25/35/40
weights, two override rules, thresholds 65/35) that turned out to be *stale* — the actual
code on GitHub didn't match some of what was claimed, and separately the fusion design
itself was reworked through discussion and real testing after that. **This version of the
file reflects what the code actually does, confirmed by running real test cases through
the live FastAPI app**, not just a design intention. If you're picking this project up in
a new chat: don't trust a `PROJECT_STATE.md` claim at face value — if in doubt, ask to see
the actual current file contents before writing code against it.

## What exists right now (verified against actual repo contents)

- `backend/app/services/rule_engine.py` — Phase 2. Regex-based message/URL keyword and
  structure detection, handles obfuscation (spaced/dotted/dashed letters). Working.
- `backend/app/services/ml_engine.py` — Phase 3. Loads `classifier.joblib` +
  `vectorizer.joblib` (TF-IDF + Logistic Regression), returns phishing probability
  0–100, label, and a flag if flagged. **These two model files are real, trained, and
  verified working** (see ML model section below) — they are gitignored and NOT pushed
  to GitHub; they exist only on the developer's local machine.
- `backend/app/services/threat_intel.py` — Phase 4. Google Safe Browsing v4 lookup
  (`check_safe_browsing`) + WHOIS domain-age check (`check_domain_age`), combined by
  `run_threat_intel()`. Requires a real `SAFE_BROWSING_API_KEY` in a local, gitignored
  `.env` file — `.env.example` in the repo is just the template.
- `backend/app/services/fusion_engine.py` — Phase 5, **rewritten and fixed this session**
  (see full design below).
- `backend/app/api/analyze.py` — calls all three layers + `run_fusion_engine()`, stores
  a `Scan` row, returns the fused result alongside raw per-layer breakdowns.
- `backend/app/schemas/analyze_schema.py` — `AnalyzeResponse` includes `final_risk_label:
  str`, `final_risk_score: int`, `explanation: List[str]`, **`recommendation: List[str]`**
  (changed from a single string to a list this session, to match the bullet-list UI design).
- `backend/app/db/models.py` — `Scan` table has `final_risk_label`/`final_risk_score`
  columns alongside per-layer columns. Unchanged this session.
- `backend/app/ml/train_model.py` — training script. Not re-run this session; existing
  trained model files were reused and verified directly.
- `backend/app/ml/dataset/phishing_dataset.csv` — 59,206 rows, `text`/`label` columns,
  ~60/40 safe/phishing split. Gitignored, exists locally only.
- `backend/app/ml/model/classifier.joblib` + `vectorizer.joblib` — real trained
  scikit-learn artifacts, gitignored, exist locally only. **Verified this session** by
  loading them directly and running real predictions (see below).

## Fusion engine design — FINAL, as actually implemented and tested

This is the complete, current logic in `fusion_engine.py`. Do not re-derive or re-tune
without a specific new failing test case (same rule as before — this was already revised
once this session because Case 6 below failed under the first attempt, and the fix is now
verified).

**Normalization (0–100 scale):**
- Rule score: capped at 100
- ML score: already 0–100 (phishing probability × 100)
- Threat-intel score: capped at **60** (max possible raw = 40 Safe Browsing + 20 WHOIS —
  this cap was a bug in an earlier version of this session's rewrite, wrongly set to 100;
  fixed and re-verified)

**Weights (when a URL is present):** rule 30% / ML 40% / threat-intel 30%

**No-URL case:** if `threat_label == "Not checked"` (no URL submitted at all), threat-intel's
30% weight is redistributed proportionally across rule/ML, keeping their 30:40 ratio —
effectively rule ~42.86%, ML ~57.14%.

**The ONE override (do not add more without a specific failing test case):**
A confirmed Google Safe Browsing match (`"Safe Browsing flagged" in threat_flags`) forces
`final_risk_label = "High Risk"` with a score floor of 90 — `max(round(weighted_score),
90)` — regardless of the blended score. This exists because a confirmed external
malicious-URL match is independently-verified ground truth, not a probabilistic guess like
rule/ML, and a pure blended average was letting confirmed-malicious URLs slip through as
"Safe" when the rest of the signal was weak (see Case 6 below — this is exactly the
scenario that proved the override was necessary).

**There is intentionally no second override.** An earlier design (from before this
session's rework) had a "rule+ML agreement" override (ML ≥80% + rule ≥30 → forced High
Risk, floor 70). **This was deliberately dropped** when the fusion engine was redesigned
this session — the current design is a plain weighted average plus only the one Safe
Browsing override above. Do not reintroduce the rule+ML override without a new specific
failing test case driving it.

**Final label thresholds (when the override doesn't fire):**
- `final_score >= 70` → High Risk
- `final_score >= 35` → Suspicious
- else → Safe

**Explanation generator:**
- If final label is "Safe" → empty list, no explanation panel (matches the Safe UI design:
  just a checkmark, nothing else)
- Otherwise: override note (if the Safe Browsing override fired) listed first, then flags
  pooled from threat-intel, then ML, then rule (in that priority order), capped at **4
  total lines** including the override note

**Recommendation generator:**
- High Risk → 3 canned bullets: don't click links / don't share personal or financial info
  / report and delete
- Suspicious → 3 canned bullets: verify via separate channel / avoid entering details until
  confirmed / consider reporting if unsure
- Safe → empty list, no recommendation panel

## Verified working — actual test results (this session, against real GitHub code)

All 11 cases below were run through the real `/analyze` endpoint (via FastAPI TestClient
in a sandbox clone, and independently by the developer locally with a real Safe Browsing
API key and working WHOIS access). Results matched between environments except where the
sandbox lacked a real API key/WHOIS network access (noted).

1. **Casual safe message, no URL** → Safe, score 3, no explanation/recommendation. ✅
2. **Clean URL only (wikipedia.org)** → Safe, score 0. ✅
3. **Obvious phishing message, no URL** ("URGENT!!! account suspended... click here...")
   → High Risk, score 88. ML 94.86% + multiple rule flags. ✅
4. **Mild/borderline message, no URL** ("Please confirm your account details...")
   → Suspicious, score 42. ML 59.16% + 2 rule flags. Confirms the 35 threshold behaves
   sensibly on a genuinely middling case. ✅
5. **Suspicious-structured URL only, no message** (`secure-login-verify-account.xyz`)
   → Safe, score 16 (dev's real run). Rule layer fires (no HTTPS, hyphens, bad TLD,
   keywords = raw 55) but with no message (ML=0) and no confirmed threat-intel hit, the
   blended score alone isn't enough to cross 35. **This is expected, not a bug** — the tool
   is not claiming this URL is definitively safe, just that rule-only signal without ML or
   external confirmation doesn't meet the Suspicious bar under the agreed weights.
6. **Google's official Safe Browsing malware test URL** (`testsafebrowsing.appspot.com/s/malware.html`)
   → **This is the key test case.** First attempt (before the fix): Safe, score 20 — a
   confirmed-malicious URL labeled Safe, with a silent explanation/recommendation. This was
   treated as a real failure (see below), not an acceptable edge case. After the fix
   (threat cap corrected to 60 + Safe Browsing override reinstated): **High Risk, score 90**,
   override note listed first in explanation. ✅ Confirmed fixed, both via direct function
   simulation and the developer's real run with their actual API key.
7. **Recently-registered domain (WHOIS age test)** → dev's sandbox/local WHOIS lookup
   failed (`PywhoisError`) rather than confirming age — WHOIS reliability against real
   registrars needs a bit more real-world exercising, but the failure mode is handled
   gracefully (never crashes `/analyze`, just skips with a flag). Not blocking Phase 5.
8. **Phishing message + Safe Browsing malware URL combined** → High Risk, score 90 (override
   fired), explanation correctly ordered: override note → Safe Browsing flag → WHOIS-fail
   flag → ML flag (rule flags didn't fit in the 4-slot cap, correct behavior). ✅
9. **Suspicious message + suspicious-but-clean URL** (`bit.ly` shortener, no Safe Browsing
   hit) → Suspicious, score 46, no override (correctly not triggered — URL came back
   "Clean", not flagged). ✅
10. **Empty request body `{}`** → 422 validation error, "At least one of 'message' or
    'url' must be provided." ✅ Pydantic validator working as designed.
11. **Whitespace-only message `"   "`** → Safe, score 18. Doesn't crash; ML gave a
    nonzero-but-low score (30.69%) on essentially meaningless input — worth knowing this
    isn't validated as "empty" by the schema (only a literal missing/None value is
    rejected), but doesn't cause any errors either. Not treated as a bug, just documented
    behavior.

**Net result: after the fix, all 11 cases behave correctly and consistently. Case 6 was
the one real failure found and fixed this session (threat-intel normalization cap bug +
missing Safe Browsing override), fully verified afterward with no regressions to any other
case.**

## ML model — verified working this session
- Real dataset (`phishing_dataset.csv`, 59,206 rows) and real trained artifacts
  (`classifier.joblib`, `vectorizer.joblib`) were provided and tested directly (not just
  assumed from `train_model.py` existing).
- Loaded and ran real predictions: obvious phishing → 92–96% confidence; casual/safe
  messages → 2–6% confidence. Sensible, working classifier.
- **scikit-learn version note:** the model was trained on and must be loaded with
  **scikit-learn 1.7.2** (already pinned in `requirements.txt`). An attempt to retrain on
  1.8.0 broke compatibility with other dependencies (uvicorn et al.) — **stay on 1.7.2
  everywhere** (local venv, any deployment target). Do not upgrade scikit-learn without
  re-testing the full dependency chain.
- Dataset and model files are correctly gitignored and were never pushed to GitHub — they
  exist only on the developer's local machine. Anyone continuing this project in a fresh
  environment (a new clone, a new deploy target, a new chat's sandbox) will need these
  files provided again to actually exercise the ML layer; without them, `ml_engine.py`
  degrades gracefully to `ml_label: "Unknown"` rather than crashing.

## Confirmed decisions (do not re-litigate these)
- Project name: **ThinkBeforeClick**
- No user accounts or login — fully anonymous, stateless
- "Report this message" feeds anonymized data into future ML retraining (Phase 6 work,
  `/report` endpoint still an empty stub)
- Extension model: Tier 1 passive local-rules-only scanning (always on, no API calls) +
  Tier 2 active popup deep-check (full pipeline via backend API) — not built yet, comes
  after the web app per build order
- Detection pipeline: rule-based + ML/NLP + threat-intel, combined by the fusion engine
  (Phase 5, now complete, corrected design above)
- Build order: **Backend API → Web App (deployed to Render) → Browser Extension**
- We move phase by phase, testing each phase before starting the next
- Backend framework: **FastAPI** (not Flask)
- Database: **SQLite**, tables for `scans` and `reports`
- Single venv at project root, not per-folder
- ML classifier: TF-IDF (unigrams+bigrams) + Logistic Regression, `class_weight="balanced"`,
  0.5 probability threshold. scikit-learn version pinned to **1.7.2** — do not upgrade
  without re-testing the whole dependency chain (see ML model section above)
- Threat-intel: Google Safe Browsing API v4, WHOIS via `python-whois`, "new domain"
  threshold under 180 days
- **Fusion engine weighting is final:** rule 30% / ML 40% / threat-intel 30% when a URL is
  present; dynamic reweighting when no URL; **one** Safe Browsing override (floor 90); NO
  rule+ML agreement override (deliberately removed this session); final thresholds ≥70 High
  Risk, ≥35 Suspicious; explanation capped at 4 lines; recommendation is a list, not a
  string. These values are tuned against the real test cases documented above — don't
  re-tune without a new specific failing test case
- `.env.example` stays as the untouched template in the repo; the real, gitignored `.env`
  (with a real `SAFE_BROWSING_API_KEY`) lives only on the developer's machine
- The GitHub project connector in Claude.ai does **not** auto-sync — it requires a manual
  "Sync now" click, and even then only pulls file names/contents on the configured branch,
  no commit history/metadata. Don't assume a new chat's view of the repo is current;
  verify against the developer directly or by cloning the public repo URL if needed.

## Frontend plan (Phase 6 — not started yet, but fully designed)

The developer has already provided full visual reference designs and a confirmed flow.
Frontend work should follow this exactly — do not redesign from scratch:

1. **Landing/intro (0–4s):** matrix-style falling-character rain background (continuous,
   runs behind every subsequent stage). "THINK BEFORE CLICK" neon-outlined box appears with
   a blinking/glitch animation for exactly 4 seconds, then glitches out and disappears.
2. **Skull reveal:** screen resolves to a skull silhouette against the matrix rain, mouth
   closed, brief idle pause.
3. **Mouth opens, input dialog appears (2-second reveal animation):** skull's mouth
   animates open over 2 seconds; a "SCAN URL" field + "PASTE MSG" textarea + "THINK" button
   fade/scale in inside the opening mouth. **Once revealed, the dialog stays open
   indefinitely** — no timeout, no auto-dismiss. It waits for the user to type and click
   "THINK" whenever they're ready.
4. **On "THINK" click:** frontend calls `POST /analyze` with whatever message/URL was
   entered. Some kind of "processing" visual state should show while waiting (e.g. a
   scanning-line effect), not a frozen blank screen.
5. **Verdict screen:** one reusable card component, three visual themes driven by
   `final_risk_label`:
   - **High Risk:** red glitchy warning triangle, "High Risk" label, score badge, "Why
     Risky" bullets (from `explanation`), "Recommendation" bullets (from `recommendation`)
   - **Suspicious:** same layout, amber/yellow theme, "Why Suspicious?" heading
   - **Safe:** green checkmark, "Safe" label, **no bullet lists at all** (matches the
     reference design — Safe is deliberately simpler)

All of stages 1–4 are pure frontend/animation work with zero backend dependency and can be
built immediately. Stage 5's content (explanation/recommendation bullets) now has real,
correct backend data behind it as of this session's fusion engine fix — this was
specifically the blocker that made building Stage 5 premature before now.

## Next step
**Phase 6 — Web App Frontend**, following the design above:
- 6.1 Analyzer page: full stage 1–5 flow (matrix rain intro → skull reveal → mouth-open
  input dialog → processing state → verdict card), wired to the real `/analyze` response
  shape (`final_risk_label`, `final_risk_score`, `explanation: List[str]`,
  `recommendation: List[str]`)
- 6.2 "Report this message" flow wired to the `/report` endpoint (`/report` is still an
  empty stub — this is new backend work too, not just frontend)
- 6.3 "How it works" page explaining the 3-layer pipeline + fusion engine in plain language
- 6.4 Responsive/mobile-friendly layout
- 6.5 Connect frontend to backend, full local end-to-end test

## Notes for continuing this project in a new chat
- Do not re-ask about accounts, hosting choice, ML approach, build order, venv setup, Safe
  Browsing API version, or fusion engine weighting — all decided and verified above
- Do not revert to Flask or reintroduce the hackathon's keyword-only logic
- Do not re-tune the fusion engine's weights, thresholds, or the single Safe Browsing
  override without a specific new failing test case — see the verified test cases above
  before assuming something is broken
- Do not reintroduce the old "rule+ML agreement" override — it was deliberately removed
- The `/report` endpoint is still an empty stub — Phase 6 work, not done yet
- Do not build the browser extension yet — Phase 6 (web app) comes first
- The ML model/dataset files are gitignored and will NOT be present in a fresh clone or a
  new chat's sandbox — they must be re-provided by the developer if the ML layer needs to
  be exercised again (e.g. re-testing, retraining)
- Before writing code against this file's claims in a brand-new chat, consider asking the
  developer to confirm the actual current file contents (via direct paste/upload, or a
  fresh `git clone` of the public repo URL) rather than trusting this document blindly —
  this exact file drifted from reality once already in this project's history
- Confirm which phase we're on before generating code