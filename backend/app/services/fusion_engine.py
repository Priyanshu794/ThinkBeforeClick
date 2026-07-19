# Phase 5: combines rule_engine + ml_engine + threat_intel into one
# risk score, label, explanation, and recommendation
from typing import Dict, List

# Layer weights — how much each layer contributes to the final fused score
# WHEN ALL THREE LAYERS HAVE A SIGNAL. Threat-intel gets the highest weight
# since it's independently-verified external ground truth.
WEIGHT_RULE = 0.25
WEIGHT_ML = 0.35
WEIGHT_THREAT = 0.40

RULE_SCORE_CAP = 100
THREAT_SCORE_CAP = 60

HIGH_RISK_THRESHOLD = 65
SUSPICIOUS_THRESHOLD = 35

# Rule+ML agreement override: if both independently agree this looks like
# phishing, that's strong enough to force High Risk even without external
# confirmation (e.g. a brand-new phishing domain Safe Browsing hasn't
# indexed yet). Optimizes for recall per the Phase 3 decision.
ML_AGREEMENT_THRESHOLD = 80    # ML confidence %
RULE_AGREEMENT_THRESHOLD = 30  # rule score


def _normalize(score: float, cap: float) -> float:
    if cap <= 0:
        return 0.0
    return min(max(score, 0), cap) / cap * 100


def run_fusion_engine(
    rule_score: int,
    rule_flags: List[str],
    ml_score: float,
    ml_label: str,
    ml_flags: List[str],
    threat_score: int,
    threat_label: str,
    threat_flags: List[str],
) -> Dict:
    rule_norm = _normalize(rule_score, RULE_SCORE_CAP)
    ml_norm = _normalize(ml_score, 100)
    threat_norm = _normalize(threat_score, THREAT_SCORE_CAP)

    # If there was no URL to check at all, threat-intel has no signal to
    # contribute — redistribute its weight proportionally across rule/ML
    # instead of letting it silently drag the ceiling down to 60.
    if threat_label == "Not checked":
        remaining = WEIGHT_RULE + WEIGHT_ML
        w_rule = WEIGHT_RULE / remaining
        w_ml = WEIGHT_ML / remaining
        weighted_score = rule_norm * w_rule + ml_norm * w_ml
    else:
        weighted_score = (
            rule_norm * WEIGHT_RULE
            + ml_norm * WEIGHT_ML
            + threat_norm * WEIGHT_THREAT
        )

    safe_browsing_hit = any("Safe Browsing flagged" in f for f in threat_flags)
    rule_ml_agree = (
        ml_label == "Phishing"
        and ml_score >= ML_AGREEMENT_THRESHOLD
        and rule_score >= RULE_AGREEMENT_THRESHOLD
    )

    override_note = None
    if safe_browsing_hit:
        final_label = "High Risk"
        final_score = max(round(weighted_score), 90)
        override_note = "Confirmed by Google Safe Browsing — this overrides the blended score."
    elif rule_ml_agree:
        final_label = "High Risk"
        final_score = max(round(weighted_score), 70)
        override_note = (
            "Rule-based and ML layers both independently flagged this as phishing "
            "with high confidence — this overrides the blended score."
        )
    else:
        final_score = round(weighted_score)
        if final_score >= HIGH_RISK_THRESHOLD:
            final_label = "High Risk"
        elif final_score >= SUSPICIOUS_THRESHOLD:
            final_label = "Suspicious"
        else:
            final_label = "Safe"

    explanation = _build_explanation(
        rule_score, rule_flags, ml_score, ml_label, ml_flags,
        threat_score, threat_label, threat_flags, override_note,
    )
    recommendation = _build_recommendation(final_label, safe_browsing_hit)

    return {
        "final_risk_label": final_label,
        "final_risk_score": final_score,
        "explanation": explanation,
        "recommendation": recommendation,
    }


def _build_explanation(
    rule_score, rule_flags, ml_score, ml_label, ml_flags,
    threat_score, threat_label, threat_flags, override_note,
) -> List[str]:
    lines: List[str] = []

    if override_note:
        lines.append(override_note)

    if rule_flags:
        lines.append(f"Rule-based layer (score {rule_score}): " + "; ".join(rule_flags))
    else:
        lines.append(f"Rule-based layer (score {rule_score}): no suspicious patterns found")

    lines.append(f"ML/NLP layer: classified as '{ml_label}' (confidence {ml_score})")
    if ml_flags:
        lines.append("ML layer notes: " + "; ".join(ml_flags))

    if threat_flags:
        lines.append(f"Threat-intel layer (score {threat_score}): " + "; ".join(threat_flags))
    else:
        lines.append(f"Threat-intel layer: {threat_label}")

    return lines


def _build_recommendation(final_label: str, safe_browsing_hit: bool) -> str:
    if final_label == "High Risk":
        if safe_browsing_hit:
            return (
                "Do not click this link or respond to this message. It has been "
                "confirmed malicious by Google Safe Browsing. Delete it and report "
                "it if it came through a school or work account."
            )
        return (
            "Do not click any links, reply, or share personal/financial information. "
            "Multiple detection layers flagged this as highly suspicious — treat it "
            "as phishing."
        )
    elif final_label == "Suspicious":
        return (
            "Proceed with caution. Don't click links or share sensitive information "
            "until you've verified this through an official, separate channel "
            "(e.g. calling the organization directly using a number you look up yourself)."
        )
    else:
        return (
            "No strong red flags found. Still, always verify unexpected requests for "
            "money, login details, or personal information through an official channel."
        )