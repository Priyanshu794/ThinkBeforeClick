# Phase 3: loads trained classifier (classifier.joblib), returns ML confidence score
import os
from typing import Tuple, List

import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/app
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model", "classifier.joblib")
VECTORIZER_PATH = os.path.join(BASE_DIR, "ml", "model", "vectorizer.joblib")

_model = None
_vectorizer = None
_load_error = None


def _load_model():
    """Lazy-load the classifier + vectorizer once, on first use."""
    global _model, _vectorizer, _load_error
    if _model is not None and _vectorizer is not None:
        return
    try:
        _model = joblib.load(MODEL_PATH)
        _vectorizer = joblib.load(VECTORIZER_PATH)
    except Exception as e:  # noqa: BLE001 - we want to degrade gracefully, not crash /analyze
        _load_error = str(e)


def analyze_message_ml(message: str) -> Tuple[float, str, List[str]]:
    """
    Runs the trained TF-IDF + Logistic Regression classifier on a message.

    Returns (ml_score, ml_label, ml_flags):
      - ml_score: phishing-class probability as a 0-100 int-friendly float
      - ml_label: "Safe" or "Phishing" based on a 0.5 probability threshold
      - ml_flags: human-readable notes (e.g. if the model couldn't load)

    Only handles `message` text. URL-only requests get a neutral score (0)
    since this model was trained on message/email body text, not URLs —
    URL signal is covered by the rule engine's analyze_url() and will be
    covered by the threat-intel layer in Phase 4.
    """
    if not message:
        return 0.0, "Safe", []

    _load_model()
    if _model is None or _vectorizer is None:
        return 0.0, "Unknown", [f"ML model unavailable: {_load_error or 'not loaded'}"]

    vec = _vectorizer.transform([message])
    proba = _model.predict_proba(vec)[0]
    # class order matches training labels: 0 = safe, 1 = phishing
    phishing_proba = float(proba[1])

    ml_score = round(phishing_proba * 100, 2)
    ml_label = "Phishing" if phishing_proba >= 0.5 else "Safe"

    flags: List[str] = []
    if phishing_proba >= 0.5:
        flags.append(f"ML classifier flagged this message as phishing-like (confidence {ml_score}%)")

    return ml_score, ml_label, flags
