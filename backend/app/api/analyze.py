from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.analyze_schema import AnalyzeRequest, AnalyzeResponse
from app.db.database import get_db
from app.db.models import Scan
from app.services.rule_engine import run_rule_engine
from app.services.ml_engine import analyze_message_ml
from app.services.threat_intel import run_threat_intel

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    rule_result = run_rule_engine(message=payload.message, url=payload.url)
    ml_score, ml_label, ml_flags = analyze_message_ml(payload.message)
    threat_result = run_threat_intel(url=payload.url)

    scan = Scan(
        message=payload.message,
        url=payload.url,
        risk_label=rule_result["rule_label"],
        risk_score=rule_result["rule_score"],
        ml_label=ml_label,
        ml_score=ml_score,
        threat_label=threat_result["threat_label"],
        threat_score=threat_result["threat_score"],
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
        message_received=payload.message,
        url_received=payload.url,
        note="Phase 4: rule + ML + threat-intel layers returned side by side, unfused. Fusion engine is Phase 5.",
    )