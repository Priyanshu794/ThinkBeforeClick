# Phase 5: combines rule_engine + ml_engine + threat_intel into one
# risk score, label, explanation, and recommendation
#
# Design (finalized in project discussion, see PROJECT_STATE.md):
#   - Weights when a URL is present: rule 30% / ML 40% / threat-intel 30%
#   - When no URL is given, threat-intel's 30% is redistributed proportionally
#     across rule/ML (kept at their 30:40 ratio -> ~42.86% / ~57.14%)
#   - Threat-intel raw score caps at 60 (Safe Browsing 40 + WHOIS 20 max),
#     normalized against that real ceiling, not 100.
#   - ONE override: a confirmed Google Safe Browsing match is independently-
#     verified ground truth, not a probabilistic guess like rule/ML — it
#     forces final_label = "High Risk" with a score floor of 90, regardless
#     of the blended score. No other overrides (e.g. no rule+ML agreement
#     override). Added after Case 6 testing showed a confirmed-malicious
#     URL landing as "Safe" under the pure blended score alone.
#   - Thresholds on the final 0-100 score (when the override doesn't fire):
#     >=70 High Risk, >=35 Suspicious, else Safe
#   - Explanation: top 4 flags pooled from whichever layers actually fired,
#     ordered threat-intel first (external ground truth), then ML, then rule.
#     Override reason (if fired) is listed first of all. Empty if final
#     label is Safe.
#   - Recommendation: a short canned bullet list keyed only off the final
#     label. Empty if final label is Safe.
from typing import Dict, List

WEIGHT_RULE = 0.30
WEIGHT_ML = 0.40
WEIGHT_THREAT = 0.30

RULE_SCORE_CAP = 100
THREAT_SCORE_CAP = 60  # Safe Browsing (40) + WHOIS (20) max possible raw score

HIGH_RISK_THRESHOLD = 70
SUSPICIOUS_THRESHOLD = 35

# How many flags to surface in the explanation panel, max.
EXPLANATION_FLAG_LIMIT = 4

# Safe Browsing confirmed-match override: score floor when it fires.
SAFE_BROWSING_OVERRIDE_FLOOR = 90


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

    # No URL submitted at all -> threat-intel has no signal. Redistribute its
    # weight proportionally across rule/ML instead of zeroing it out, so a
    # message-only submission isn't artificially capped.
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

    override_note = None
    if safe_browsing_hit:
        final_label = "High Risk"
        final_score = max(round(weighted_score), SAFE_BROWSING_OVERRIDE_FLOOR)
        override_note = "Confirmed by Google Safe Browsing — this overrides the blended score."
    else:
        final_score = round(weighted_score)
        if final_score >= HIGH_RISK_THRESHOLD:
            final_label = "High Risk"
        elif final_score >= SUSPICIOUS_THRESHOLD:
            final_label = "Suspicious"
        else:
            final_label = "Safe"

    explanation = _build_explanation(
        final_label, rule_flags, ml_flags, threat_flags, override_note
    )
    recommendation = _build_recommendation(final_label)

    return {
        "final_risk_label": final_label,
        "final_risk_score": final_score,
        "explanation": explanation,
        "recommendation": recommendation,
    }


def _build_explanation(
    final_label: str,
    rule_flags: List[str],
    ml_flags: List[str],
    threat_flags: List[str],
    override_note: str = None,
) -> List[str]:
    # Safe verdicts show no explanation panel at all (matches the "Safe" UI
    # design: just a checkmark, no bullet list).
    if final_label == "Safe":
        return []

    lines: List[str] = []
    if override_note:
        lines.append(override_note)

    # Pool remaining flags from layers that actually fired, ordered
    # threat-intel first (independently-verified external signal), then ML,
    # then rule. Cap total lines (including the override note) at the limit.
    pooled = list(threat_flags) + list(ml_flags) + list(rule_flags)
    remaining_slots = EXPLANATION_FLAG_LIMIT - len(lines)
    lines.extend(pooled[:remaining_slots])
    return lines


def _build_recommendation(final_label: str) -> List[str]:
    if final_label == "High Risk":
        return [
            "Do not click any links in this message.",
            "Do not share personal, financial, or login details.",
            "Report this message and delete it.",
        ]
    elif final_label == "Suspicious":
        return [
            "Verify the sender through a separate, trusted channel.",
            "Avoid entering any personal details until confirmed.",
            "Consider reporting this if you're unsure.",
        ]
    else:
        return []