# Phase 1: SQLAlchemy models for `scans` and `reports` tables
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.db.database import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    risk_label = Column(String, nullable=True)      # Safe / Suspicious / High Risk (set from Phase 5 onward)
    risk_score = Column(Integer, nullable=True)      # placeholder numeric score
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    reason = Column(Text, nullable=True)             # optional user note on why they're reporting
    created_at = Column(DateTime(timezone=True), server_default=func.now())