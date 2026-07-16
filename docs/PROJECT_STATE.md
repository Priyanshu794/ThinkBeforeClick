# ThinkBeforeClick — Project State

_Last updated: end of planning stage, before Phase 1 begins._

## Where we are
Planning is complete. No code has been written yet. This is a full rebuild from scratch —
nothing from the earlier hackathon prototype is being reused.

## What exists right now
- `AI_Shield_Project_Blueprint.md` — idea, how it works, high-level phases, architecture diagrams
- `phases.md` — detailed 9-phase breakdown with sub-steps, and the full target file structure
- This file (`PROJECT_STATE.md`) — nothing to report yet, will be updated after each phase

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
- Backend framework: **FastAPI** (not Flask — chosen for validation, async, and auto docs)
- Database: **SQLite** to start, tables for `scans` and `reports`

## Target file structure
See `phases.md` for the complete folder tree (backend/, webapp/, extension/, docs/).

## Next step
**Phase 1 — Backend Foundation.** Build the project skeleton:
- `backend/app/main.py`, `api/health.py`, `api/analyze.py` (placeholder response),
  `schemas/analyze_schema.py`, `db/` setup with `scans` and `reports` tables
- Nothing clever yet — just a real, testable, empty skeleton per phases.md §Phase 1

## Notes for continuing this project in a new chat
- Do not re-ask about accounts, hosting choice, ML approach, or build order — all decided above
- Do not revert to Flask or reintroduce the hackathon's keyword-only logic
- Confirm which phase we're on before generating code
