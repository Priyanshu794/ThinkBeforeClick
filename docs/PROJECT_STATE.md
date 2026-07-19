# ThinkBeforeClick — Project State

_Last updated: end of Phase 5, confirmed working._

## Where we are
Phase 1 (Backend Foundation), Phase 2 (Rule-Based Detection Layer), Phase 3 (ML/NLP
Layer), Phase 4 (Threat-Intelligence Layer), and Phase 5 (Fusion Engine) are all complete
and verified working. Ready to begin Phase 6 (Web App Frontend).

## What exists right now
Everything from Phases 1–4 (rule engine, ML classifier, threat-intel layer), plus new
Phase 5 additions:

- `backend/app/services/fusion_engine.py` — Phase 5 core logic:
  - Normalizes each layer's raw score to a 0–100 scale (rule capped at 100, ML already
    0–100, threat-intel capped at 60 since max possible is 40 Safe Browsing + 20 WHOIS).
  - Base weighting when all three layers have a signal: rule 25% / ML 35% / threat-intel
    40% (threat-intel weighted highest as independently-verified external ground truth).
  - **Dynamic reweighting:** if no URL was submitted at all (`threat_label == "Not
    checked"`), threat-intel's 40% weight is redistributed proportionally across rule
    and ML instead of just zeroing it out — otherwise message-only phishing could never
    exceed a 60/100 ceiling regardless of how obvious it was.
  - **Override 1 — Safe Browsing confirmed match:** forces `final_risk_label = "High
    Risk"` and a score floor of 90, regardless of the blended score. This is
    independently-verified ground truth and takes priority over everything else.
  - **Override 2 — rule+ML agreement:** if the ML classifier says "Phishing" at ≥80%
    confidence AND the rule engine also scored ≥30, forces `final_risk_label = "High
    Risk"` with a score floor of 70. Added after testing showed that obvious phishing
    (both brand-new unindexed phishing domains and message-only phishing with no URL at
    all) was landing at "Suspicious" instead of "High Risk" purely because threat-intel
    had no way to confirm it yet. This override reflects the Phase 3 "optimize for
    recall" decision — two independent detection methods agreeing is strong enough
    signal on its own, without waiting on external threat-intel to catch up.
  - Builds a plain-language `explanation` (list of strings, one per layer, with the
    override reason listed first if one fired) and a `recommendation` string tailored to
    the final label.
  - Final label thresholds (when no override fires): score ≥65 → High Risk, ≥35 →
    Suspicious, else Safe.
- `backend/app/api/analyze.py` — now also calls `run_fusion_engine()`, passing in all
  three layers' outputs, and returns the fused result alongside the raw per-layer data.
- `backend/app/schemas/analyze_schema.py` — `AnalyzeResponse` gained `final_risk_label:
  str`, `final_risk_score: int`, `explanation: List[str]`, `recommendation: str`,
  additive to all Phase 2/3/4 fields.
- `backend/app/db/models.py` — `Scan` table gained `final_risk_label` (String) and
  `final_risk_score` (Integer) columns, additive to all prior columns.
- `backend/thinkbeforeclick.db` — deleted and recreated during Phase 5 setup so SQLite
  would pick up the two new columns (dev DB, no data loss of consequence).

## Verified working (Phase 5 tests passed)
- **Known-safe** (casual message + `https://www.wikipedia.org`) → `final_risk_label:
  "Safe"`, `final_risk_score: 2`. All three layers clean, no override fires.
- **Obfuscated urgent/account/suspended message, no URL** → `final_risk_label: "High
  Risk"`, `final_risk_score: 70`. Threat-intel correctly shows "Not checked" (weight
  redistributed to rule+ML), and the rule+ML agreement override fired since ML
  confidence (84%) and rule score (50) both cleared their thresholds.
- **Google's official Safe Browsing test URL** → `final_risk_label: "High Risk"`,
  `final_risk_score: 90`. Safe Browsing override fired and took priority; explanation's
  first line correctly names the override reason.
- **Fake Apple ID phishing message + hyphen-stuffed unindexed fake domain** →
  `final_risk_label: "High Risk"`, `final_risk_score: 70`. Safe Browsing and WHOIS both
  came back clean/unconfirmed (realistic — brand-new phishing domains often aren't
  blacklisted yet), but the rule+ML agreement override correctly still caught it. This
  was the specific case that proved the fix was needed and working.
- Confirmed the fix didn't break the known-safe case or the Safe-Browsing-confirmed
  case — re-ran both after the fusion engine update, both still correct.

## Confirmed decisions (do not re-litigate these)
- Project name: **ThinkBeforeClick**
- No user accounts or login — fully anonymous, stateless
- "Report this message" feeds anonymized data into future ML retraining
- Extension model: Tier 1 passive local-rules-only scanning (always on, no API calls) +
  Tier 2 active popup deep-check (full pipeline via backend API)
- Detection pipeline: rule-based layer + ML/NLP layer (TF-IDF + Logistic Regression) +
  threat-intel layer (Google Safe Browsing + WHOIS), combined by the fusion engine
  (Phase 5, now complete)
- Build order: **Backend API → Web App (deployed to Render) → Browser Extension**
- We move phase by phase, testing each phase before starting the next
- Backend framework: **FastAPI** (not Flask)
- Database: **SQLite**, tables for `scans` and `reports`
- Single venv at project root, not per-folder
- ML classifier: TF-IDF (unigrams+bigrams) + Logistic Regression, `class_weight="balanced"`,
  0.5 probability threshold for Safe/Phishing — trained to favor recall over precision.
  Settled; don't re-litigate or "upgrade" the model type
- Threat-intel: Google Safe Browsing API v4 (current, non-legacy), threat score 40 for
  any match; WHOIS via `python-whois`, "new domain" threshold under 180 days, score 20
- **Fusion engine weighting is now final, not a placeholder:** rule 25% / ML 35% /
  threat-intel 40% when all layers have a signal; dynamic reweighting when no URL is
  present; Safe Browsing override (score floor 90); rule+ML agreement override (ML ≥80%
  phishing confidence AND rule score ≥30, score floor 70); final thresholds 65 = High
  Risk, 35 = Suspicious. These values were tuned against real test cases (see above) —
  don't re-tune without a specific failing test case driving it
- `/analyze` now returns fully fused results (`final_risk_label`, `final_risk_score`,
  `explanation`, `recommendation`) alongside the raw per-layer breakdowns — this is the
  complete, explainable pipeline output described in the blueprint
- `.env.example` stays as the untouched template in the repo; the real, gitignored
  `.env` is where actual secrets live

## Target file structure
See `phases.md` for the complete folder tree (backend/, webapp/, extension/, docs/).

## Next step
**Phase 6 — Web App Frontend.**
- 6.1 Analyzer page: message + URL input, results panel (final score, per-layer
  breakdown, flags, explanation, recommendation)
- 6.2 "Report this message" flow wired to the `/report` endpoint
- 6.3 "How it works" page explaining the 3-layer pipeline + fusion engine in plain language
- 6.4 Responsive/mobile-friendly layout
- 6.5 Connect frontend to backend, full local end-to-end test

## Notes for continuing this project in a new chat
- Do not re-ask about accounts, hosting choice, ML approach, build order, venv setup,
  Safe Browsing API version, or fusion engine weighting — all decided and tuned above
- Do not revert to Flask or reintroduce the hackathon's keyword-only logic
- Do not re-tune the fusion engine's weights, overrides, or thresholds without a
  specific new failing test case — the current values were arrived at through iterative
  testing, not arbitrary
- The `/report` endpoint (`backend/app/api/report.py`) is still an empty stub — it's
  Phase 6 work (6.2), not done yet
- Do not build the browser extension yet — Phase 6 (web app) comes first per the
  confirmed build order
- Confirm which phase we're on before generating code
