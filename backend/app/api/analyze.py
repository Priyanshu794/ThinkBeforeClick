from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.analyze_schema import AnalyzeRequest, AnalyzeResponse
from app.db.database import get_db
from app.db.models import Scan
from app.services.rule_engine import run_rule_engine

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    result = run_rule_engine(message=payload.message, url=payload.url)

    scan = Scan(
        message=payload.message,
        url=payload.url,
        risk_label=result["rule_label"],
        risk_score=result["rule_score"],
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    return AnalyzeResponse(
        risk_label=result["rule_label"],
        risk_score=result["rule_score"],
        flags=result["rule_flags"],
        message_received=payload.message,
        url_received=payload.url,
        note="Phase 2: rule-based detection only. ML and threat-intel layers not yet integrated.",
    )