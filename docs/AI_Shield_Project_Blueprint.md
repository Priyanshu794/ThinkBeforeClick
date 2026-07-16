# AI Shield – Student Phishing Detector
## Production Build Blueprint (Web App + Browser Extension)

---

## 1. The Idea

Students receive a constant stream of messages about scholarships, internships, placements,
college fees, competitions, and government schemes. Many of these are now AI-generated and
look convincing. AI Shield helps a student check a suspicious message **before** they click a
link, make a payment, or share personal information.

Instead of a single "safe / unsafe" verdict, AI Shield runs **three independent detection
layers** and combines them into one explainable risk score:

1. **Rule-based layer** — fast, local, pattern-matching for known phishing language and URL
   structure. Zero cost, zero external calls, catches the obvious cases instantly.
2. **ML/NLP layer** — a trained text classifier (TF-IDF + Logistic Regression) that learns
   patterns from real phishing/spam data, catching cases that don't match a fixed keyword list.
3. **Threat-intelligence layer** — external checks against Google Safe Browsing, domain-age
   lookups (WHOIS), so a clean-looking but freshly-registered or blacklisted domain still
   gets caught.

A **fusion engine** combines all three into one score, one risk label (Safe / Suspicious /
High Risk), a breakdown of which layer flagged what, and a plain-language recommendation.

No accounts. No login. The tool is fully anonymous and stateless from the student's point of
view — nothing personal is ever stored. The only data retained is the scanned message/URL
content itself (not who scanned it), which feeds an opt-in **"Report this message"** pipeline
used later to retrain and improve the ML model.

---

## 2. How It Will Work

### 2.1 Web App

- Student visits the site, pastes a suspicious message and/or URL into the analyzer.
- Backend runs the full 3-layer pipeline and returns a risk score, label, per-layer breakdown,
  detected red flags, and a recommended action.
- Student can click **"Report this message"** if they believe the result is wrong or want to
  flag a new phishing pattern — this feeds the retraining dataset.
- No login, no history tied to a person. Fully stateless per visit.
- Includes a short **"How it works"** page explaining the three layers in plain language, for
  transparency and trust.

### 2.2 Browser Extension

The extension solves the real-world problem that people forget to manually check messages.
It works in **two tiers**:

**Tier 1 — Passive, always-on scanning (no click needed)**
- A lightweight content script runs quietly on webmail/webchat tabs (Gmail, Outlook Web,
  WhatsApp Web, etc.).
- It runs only the **local rule-based layer** on visible page text and links — fast, free,
  no external API calls, no data leaves the browser.
- If something looks suspicious, it visually flags it inline (a small warning icon next to
  the risky link/text) and updates a badge count on the extension icon — similar to how an
  ad-blocker shows a blocked-item count.
- This is what removes the "I forgot to check" failure mode: the warning finds the student
  instead of requiring them to seek it out.

**Tier 2 — Active, on-demand deep check**
- Clicking the flagged warning icon, or the extension icon itself, opens the full popup —
  the same analyzer UI as the web app.
- This triggers the **full pipeline** (rules + ML + threat-intel) against the backend API,
  giving the complete explainable breakdown and the report option.
- This is also how a student checks anything the passive scanner can't reach: a forwarded
  SMS, a message read aloud to them, a screenshot's text pasted in, WhatsApp mobile, etc.

**Why split it this way:** running the full ML + external threat-intel pipeline on every
link on every page would be slow, expensive (API rate limits), and would mean sending
everything a student reads to an external server. The cheap local layer handles constant
background triage for free; the full pipeline only runs when something is already suspicious
or the student actively asks — the same pattern real browser security tools use.

---

## 3. Build Phases

Backend is built first since both the web app and the extension consume the same API.

| Phase | Focus | Key Deliverables |
|---|---|---|
| **Phase 1** | Backend foundation | FastAPI project structure, `/analyze` endpoint, request validation, upgraded rule engine (regex + obfuscation handling), SQLite database for scan/report storage |
| **Phase 2** | ML layer | Collect + clean public phishing/spam datasets, train TF-IDF + Logistic Regression classifier, evaluate (precision/recall), wrap as a callable service |
| **Phase 3** | Threat-intel + fusion engine | Google Safe Browsing API integration, WHOIS domain-age check, fusion engine combining all 3 layers with weighted scoring + explanation generator |
| **Phase 4** | Web app + deployment | Rebuilt frontend calling the new API, deploy backend + frontend + database to Render, end-to-end testing with real sample messages |
| **Phase 5** | Browser extension | Manifest V3 extension: passive content-script scanner (Tier 1) + popup deep-check UI (Tier 2), pointed at the deployed backend |

**Build order confirmed:** Backend API → Web App (deployed) → Browser Extension.
Building the extension last means it targets a stable, already-tested, live API instead of a
local one that changes mid-build.

---

## 4. Architecture Flow

### 4.1 High-Level System Architecture

```
                        ┌────────────────────┐
                        │   Student / User    │
                        └──────────┬──────────┘
                                   │
                  ┌────────────────┴────────────────┐
                  ▼                                  ▼
        ┌───────────────────┐              ┌───────────────────┐
        │      Web App        │              │  Browser Extension  │
        │  (paste & analyze)  │              │ Tier 1: passive scan │
        │                    │              │ Tier 2: popup check  │
        └──────────┬─────────┘              └──────────┬──────────┘
                   │                                    │
                   └───────────────┬────────────────────┘
                                   ▼
                        ┌─────────────────────┐
                        │     Backend API       │
                        │   (FastAPI service)   │
                        └──────────┬────────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   Fusion / Risk Engine │
                        └──────────┬────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                     ▼
    ┌───────────────┐    ┌───────────────────┐   ┌────────────────────┐
    │  Rule-Based     │    │   ML/NLP Classifier │   │  Threat-Intel Layer │
    │  Layer          │    │   (TF-IDF + LogReg) │   │  (Safe Browsing,     │
    │  (regex/keyword)│    │                    │   │   WHOIS domain age)  │
    └───────────────┘    └───────────────────┘   └────────────────────┘
              │                    │                     │
              └────────────────────┴─────────────────────┘
                                   ▼
                        ┌─────────────────────┐
                        │  Combined Risk Score  │
                        │  + Explanation +      │
                        │  Recommendation       │
                        └──────────┬────────────┘
                                   ▼
                        ┌─────────────────────┐
                        │   Response to User    │
                        │  (web or extension)   │
                        └──────────┬────────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │  "Report this message"│
                        │  → stored anonymously │
                        │  → future ML retraining│
                        └─────────────────────┘
```

### 4.2 Extension-Specific Flow

```
              User opens Gmail / WhatsApp Web / Outlook Web
                                 │
                                 ▼
                 Content script scans visible page text
                                 │
                                 ▼
                  Local rule-based check (no API call)
                                 │
                     ┌───────────┴───────────┐
                     ▼                       ▼
              Nothing suspicious      Suspicious pattern found
                     │                       │
                     ▼                       ▼
              (silent, no action)   Inline warning icon shown
                                    + badge count on extension icon
                                                │
                                                ▼
                                  User clicks warning or extension icon
                                                │
                                                ▼
                                  Popup opens → full pipeline runs
                                  (rules + ML + threat-intel via backend API)
                                                │
                                                ▼
                                  Full explainable result + report option
```

### 4.3 Data Flow Summary

- **No accounts, no personal data stored.**
- Only the message/URL **content** of reported items is retained, anonymously, for
  retraining the ML layer.
- Passive extension scanning never leaves the browser (local rules only).
- Active/deep checks (web app or extension popup) send message/URL content to the backend
  API for the full pipeline, and discard it after returning the result unless the user
  explicitly reports it.

---

## 5. Confirmed Product Decisions

- No user accounts or login — fully anonymous, stateless.
- Reported messages auto-feed into future ML model retraining.
- Extension uses a hybrid model: passive always-on local scanning + active on-demand deep
  analysis via popup.
- Full rebuild from scratch — no code carried over from the earlier hackathon prototype.
- Build order: **Backend API → Web App (deployed) → Browser Extension.**
