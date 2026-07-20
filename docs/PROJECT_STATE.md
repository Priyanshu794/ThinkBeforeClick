# ThinkBeforeClick — Project State

_Last updated: end of Phase 6 (web app frontend), core analyzer flow built, tested against
the real backend, and confirmed working._

## Where we are
Phases 1–5 (backend: rule engine, ML classifier, threat-intel, fusion engine) remain
complete and verified — unchanged this session. **Phase 6 (web app frontend) — core
analyzer flow — is now built and confirmed working end-to-end against the real, running
FastAPI backend.**

`how-it-works.html` and `report.js` (originally listed as 6.2/6.3) have been **dropped from
scope by product decision** — not being built. Treat Phase 6 as complete once the analyzer
flow (this session's work) is considered done; do not build these two files unless
explicitly asked again in a future session.

## What was built this session — `webapp/`

- `webapp/index.html` — full page markup for the analyzer flow (see "Frontend flow" below)
- `webapp/static/css/style.css` — all styling: matrix-green CSS variable (`--matrix-green:
  #39FF14`), verdict card themes (red/amber/green), terminal-panel dialog styling, glitch
  keyframes, pure-CSS scanline overlay
- `webapp/static/js/analyzer.js` — Canvas-based matrix rain engine (baseline + boosted
  speed states), GSAP-driven stage sequencing, fetch call to `POST /analyze`, verdict
  rendering
- `webapp/static/js/vendor/gsap.min.js` — **GSAP is self-hosted, not loaded from a CDN.**
  This was a deliberate fix: loading GSAP from `cdnjs.cloudflare.com` was silently blocked
  by browser tracking-prevention/ad-blocker behavior in testing, which broke every
  animation with no visible error. Self-hosting removes this failure mode entirely. If
  `analyzer.js` runs and GSAP is missing, it now fails loudly with an on-screen message
  instead of silently breaking (see `DOMContentLoaded` handler in `analyzer.js`).

**Do not switch GSAP back to a CDN `<script>` tag** — this was tried and caused a real,
hard-to-diagnose bug (all layers appearing at once, no animation, no error) at
`cdnjs.cloudflare.com` specifically. Self-hosted is the confirmed-working approach.

## Frontend flow — as actually built (revised from original design)

The originally-planned skull/jaw visual concept (Stages 2–3 of the original design) was
**dropped entirely this session**, replaced with a simpler terminal-panel reveal. Reasons:

1. The AI-generated skull layer assets (skull-head, jaw-open/closed, teeth, glow, matrix
   overlay, noise — 7 PNG files) were tested and found to have **zero real alpha
   transparency** — every pixel in every file was fully opaque (verified programmatically:
   alpha histogram showed 0 transparent pixels across all 7 files). Each file was actually
   a screenshot crop of a reference/spec sheet, complete with baked-in labels ("2. JAW
   (CLOSED)"), a border frame, and a checkerboard graphic drawn as solid pixels rather than
   real transparency. This made them fundamentally unusable for layered compositing no
   matter how the CSS/JS was written.
2. Given that, the product decision was made to **remove the skull concept entirely**
   rather than chase further asset regeneration.

**Current actual flow:**
1. **Stage 1 — Intro (4 seconds):** matrix rain runs continuously in the background (Canvas,
   never resets). "THINK BEFORE CLICK" neon box glitches/jitters for 4 seconds, then does
   one hard glitch-out and disappears. (Unchanged from original design.)
2. **Stage 2 — Terminal panel reveal:** a bordered, matrix-green terminal-style panel
   glitches/scales into view (GSAP `back.out` ease) directly — no skull, no jaw, no image
   assets at all. Contains: "SCAN URL" text input, "PASTE MSG" textarea, "THINK" button.
   Stays open indefinitely once revealed — no timeout, no auto-dismiss.
3. **Stage 3 — Processing:** on "THINK" click, `POST /analyze` fires. The background rain
   visibly speeds up the instant the button is clicked (interval eased from ~45ms baseline
   to ~14ms boosted). Rain eases back to baseline once the verdict card finishes appearing
   (confirmed product decision — sustained-fast rain behind a card meant to be read calmly
   was judged worse than easing back).
4. **Stage 4 — Verdict card:** one reusable card, themed by `final_risk_label`:
   - **High Risk:** red theme, warning-triangle icon, "Why Risky" heading, explanation +
     recommendation bullets, score badge
   - **Suspicious:** identical layout, amber theme, "Why Suspicious?" heading
   - **Safe:** green checkmark (same `--matrix-green` as the rest of the app), score badge
     — **no bullet lists at all**, "Why"/"Recommendation" sections fully omitted (not
     shown-empty) per original design intent
   - "SCAN AGAIN" button resets the input fields and returns straight to Stage 2's dialog
     (does not replay the intro glitch) — a deliberate UX choice for repeat testing/use

## Known working — confirmed by direct testing against the real backend

- Full flow runs smoothly: intro → terminal reveal → dialog → processing (rain
  boost/ease) → verdict, with no animation glitches after the GSAP self-hosting fix
- Verdict rendering confirmed correct against real API responses for Safe, Suspicious, and
  High Risk labels, including correct heading text, correct theme colors, correct
  score/explanation/recommendation content pulled directly from the API response
- CORS: required `app.add_middleware(CORSMiddleware, ...)` block was added to
  `backend/app/main.py` (the import was already present, just not wired up) — confirmed
  necessary and working, since the frontend is served on a different local port
  (`localhost:5500` via `python -m http.server`) than the backend (`127.0.0.1:8000`)
- Local run procedure confirmed: two terminals — one running
  `uvicorn app.main:app --reload` from `backend/`, one running `python -m http.server 5500`
  from **inside `webapp/`** (must `cd` into the folder containing `index.html` directly,
  not a parent or child folder — this tripped up local testing once already)

## Known backend detection gaps — found via real-world (non-dummy) test cases this session

**Important: these were backend findings, not frontend bugs.** The frontend correctly
displayed every result exactly as the backend/fusion engine computed it in every case
below — confirmed by comparing frontend output against raw Swagger (`/docs`) responses
directly.

1. **Delivery/courier scam pattern** ("parcel could not be delivered... update your details
   within 12 hours... `.info` TLD") — **RESOLVED.** `rule_engine.py`'s `SUSPICIOUS_KEYWORDS`
   and `SUSPICIOUS_TLDS` lists were updated to add delivery/courier vocabulary ("parcel",
   "could not be delivered", "return to sender", "courier", etc.) and the `.info` TLD.
   Verified directly: this case's raw rule score went from ~10 to 80, and the developer
   confirmed the real end-to-end result (blended through ML + threat-intel) now looks
   correct. A legit control case (official fee-reminder message mentioning "portal") was
   also re-tested and confirmed to still correctly score 0/Safe — no false-positive
   regression introduced.

2. **Fake exam-results/portal-login scam** ("Your semester result has been declared. Login
   to check your marks... university-results-portal.xyz/login") — **RESOLVED.** Same
   `rule_engine.py` update added "provisional certificate", "portal closes", "results
   portal" to `SUSPICIOUS_KEYWORDS` and "track"/"parcel"/"delivery"/"shipment"/"results" to
   `SUSPICIOUS_URL_KEYWORDS`. Verified: raw rule score went from a handful of points to 60.
   Developer confirmed the real result now looks correct.

3. **Bank OTP phishing, message-only** ("account will be temporarily blocked... share the
   OTP... immediately") → came back **Suspicious** (score 65), not **High Risk** as a human
   would likely judge it. **NOT YET ADDRESSED.** Multiple rule keywords do fire ("blocked,"
   "unusual activity," "OTP," "immediately"), and with no URL submitted the fusion engine
   reweights to ~43% rule / ~57% ML — but the blended score landed just under the 70
   High-Risk threshold. This is a near-miss, not a keyword-coverage gap — a keyword-list fix
   like the one used for Cases 1/2 won't move this case, since the relevant keywords already
   match. Would need either a threshold/weighting conversation or a narrow new override
   (similar in spirit to the existing Safe Browsing override) — bigger discussion, deferred.

4. **Subtly-worded scam, no urgency/shouting** ("regarding your recent application...
   share your bank details so we can process your first stipend payment in advance") →
   came back **Safe** (score 32), not even **Suspicious**. **NOT YET ADDRESSED.** No rule
   keywords match at all; entire score rides on ML alone, which apparently doesn't rate
   calm, non-shouty phrasing as phishing-like. This is a training-data gap, not something a
   keyword-list edit can fix — would need ML training dataset additions (more "subtle/quiet"
   phishing examples) and a retrain. Deferred — bigger scope than a quick rule-engine pass.

**Current state:** Cases 1 and 2 resolved via an additive `rule_engine.py` update (keywords/
TLDs only — no reweighting, no threshold changes, no ML retraining). Cases 3 and 4 remain
open and need a separate, larger conversation before touching thresholds or the ML model.

## Confirmed decisions (carried over, still valid)
- Project name: **ThinkBeforeClick**; no accounts/login; fully anonymous, stateless
- Backend: FastAPI, SQLite, single venv at project root
- Detection pipeline: rule-based + ML/NLP + threat-intel, combined by the fusion engine
  (unchanged, still rule 30% / ML 40% / threat-intel 30%, one Safe Browsing override,
  thresholds ≥70 High Risk / ≥35 Suspicious) — **do not re-tune without deciding first**
  whether the gaps documented above warrant it
- ML model/dataset files remain gitignored, local-only — not on GitHub
- scikit-learn pinned to 1.7.2 — do not upgrade without re-testing the dependency chain
- Build order: Backend API → Web App → Browser Extension (unchanged)
- **Frontend stack (confirmed working, this session):** plain HTML/CSS/JS, Canvas for the
  matrix rain, self-hosted GSAP for animation sequencing, no frontend framework
- **`how-it-works.html` and `report.js` are out of scope** — explicit product decision this
  session, do not build unless asked again
- The GitHub project connector does not auto-sync — manual "Sync now" or direct repo clone
  needed to see current files in a new chat

## Not yet done
- Phase 6's `how-it-works.html` / `report.js` — deliberately dropped, not just deferred
- Phase 7 — Deployment (Render) — not started
- Phase 8–9 — Browser Extension — not started
- Backend detection gaps 3 & 4 (OTP-case threshold near-miss, subtle-scam ML gap) — not
  started, need a larger threshold/override or ML-retraining conversation before touching
  anything (see "Known backend detection gaps" above)

## Notes for continuing this project in a new chat
- Do not attempt to reintroduce the skull/jaw visual concept without first confirming a
  real, properly-exported, actually-transparent asset set exists — the previous attempt's
  files were confirmed (via direct alpha-channel inspection) to have zero real transparency
  and were unusable for layered compositing
- Do not switch GSAP back to a CDN `<script src>` — self-hosted at
  `webapp/static/js/vendor/gsap.min.js` is the confirmed-working setup after a CDN-based
  version caused a silent, hard-to-diagnose animation failure in real testing
- CORS middleware in `backend/app/main.py` is required for local frontend/backend testing
  across different ports — already added and confirmed working, don't remove it
- When running locally, `python -m http.server` must be started from *inside* `webapp/`
  (the folder directly containing `index.html`), not from a parent or sibling folder
- The four backend detection gaps documented above are real findings from genuine
  real-world-style test phrasing (not the earlier textbook/dummy test cases) — treat them
  as legitimate follow-up work, not noise
- Confirm which phase/task we're on before generating code