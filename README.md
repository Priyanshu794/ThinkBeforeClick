# 🛡️ ThinkBeforeClick

> Think before you click — an AI-powered phishing shield built for students.

Students get flooded with messages about scholarships 🎓, internships 💼, placements,
college fees 💳, and "guaranteed" rewards — and a growing number of them are AI-generated
phishing attempts designed to look completely legitimate.

**ThinkBeforeClick** analyzes a suspicious message or link *before* you click, pay, or
share anything — and instead of just saying "risky," it tells you exactly **why**.

---

## ✨ What makes it different

- 🧩 **Three independent detection layers**, fused into one explainable score
  - ⚡ Rule-based engine — instant, local pattern detection
  - 🧠 ML/NLP classifier — trained to catch what keywords miss
  - 🌐 Threat-intelligence checks — real-time domain & link verification
- 🔍 **Explainable by design** — every score comes with the reasons behind it, not a black box
- 🕵️ **Fully anonymous** — no accounts, no logins, nothing personal ever stored
- 🔄 **Self-improving** — reported messages anonymously feed future model retraining
- 🧭 **Two ways to protect you**
  - 🌍 A web app for manual deep-checks
  - 🧩 A browser extension that quietly watches in the background *and* lets you dig deeper on demand — so you're protected even when you forget to check

---

## 🏗️ Tech Stack

| Layer | Tech |
|---|---|
| Backend | 🐍 Python · ⚡ FastAPI |
| Detection | 📐 Regex rules · 🤖 scikit-learn (TF-IDF + Logistic Regression) · 🛰️ Google Safe Browsing + WHOIS |
| Database | 🗄️ SQLite |
| Frontend | 🌐 HTML · CSS · JavaScript |
| Extension | 🧩 Chrome Manifest V3 |
| Deployment | ☁️ Render |

---

## 🚧 Status

Actively in development, built phase-by-phase. See `docs/phases.md` for the full roadmap.

---

## 🎯 Mission

Not just to flag phishing — to help students *recognize* it themselves next time. 🎓🛡️git branch -M main
