from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.analyze_schema import AnalyzeRequest, AnalyzeResponse
from app.db.database import get_db
from app.db.models import Scan
from app.services.rule_engine import run_rule_engine
from app.services.ml_engine import analyze_message_ml
from app.services.threat_intel import run_threat_intel
from app.services.fusion_engine import run_fusion_engine

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    rule_result = run_rule_engine(message=payload.message, url=payload.url)
    ml_score, ml_label, ml_flags = analyze_message_ml(payload.message)
    threat_result = run_threat_intel(url=payload.url)

    fusion_result = run_fusion_engine(
        rule_score=rule_result["rule_score"],
        rule_flags=rule_result["rule_flags"],
        ml_score=ml_score,
        ml_label=ml_label,
        ml_flags=ml_flags,
        threat_score=threat_result["threat_score"],
        threat_label=threat_result["threat_label"],
        threat_flags=threat_result["threat_flags"],
    )

    scan = Scan(
        message=payload.message,
        url=payload.url,
        risk_label=rule_result["rule_label"],
        risk_score=rule_result["rule_score"],
        ml_label=ml_label,
        ml_score=ml_score,
        threat_label=threat_result["threat_label"],
        threat_score=threat_result["threat_score"],
        final_risk_label=fusion_result["final_risk_label"],
        final_risk_score=fusion_result["final_risk_score"],
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    return AnalyzeResponse(
        risk_label=rule_result["rule_label"],
        risk_score=rule_result["rule_score"],
        flags=rule_result["rule_flags"],
        ml_label=ml_label,
        ml_score=ml_score,
        ml_flags=ml_flags,
        threat_label=threat_result["threat_label"],
        threat_score=threat_result["threat_score"],
        threat_flags=threat_result["threat_flags"],
        final_risk_label=fusion_result["final_risk_label"],
        final_risk_score=fusion_result["final_risk_score"],
        explanation=fusion_result["explanation"],
        recommendation=fusion_result["recommendation"],
        message_received=payload.message,
        url_received=payload.url,
        note="Phase 5: fusion engine combines rule + ML + threat-intel into one final score, label, explanation, and recommendation.",
    )