# Phase 1: SQLAlchemy models for `scans` and `reports` tables
# Phase 3: added ml_score / ml_label columns (additive — existing rule_label/
# rule_score columns from Phase 2 are untouched) to store the ML layer's
# output alongside the rule engine's, ready for the fusion engine in Phase 5.
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func

from app.db.database import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    risk_label = Column(String, nullable=True)      # Safe / Suspicious / High Risk (rule engine, Phase 2)
    risk_score = Column(Integer, nullable=True)      # rule-based additive score (Phase 2)
    ml_label = Column(String, nullable=True)         # Safe / Phishing (ML classifier, Phase 3)
    ml_score = Column(Float, nullable=True)          # ML phishing-probability score 0-100 (Phase 3)
    threat_label = Column(String, nullable=True)
    threat_score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())



class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    reason = Column(Text, nullable=True)             # optional user note on why they're reporting
    created_at = Column(DateTime(timezone=True), server_default=func.now())
