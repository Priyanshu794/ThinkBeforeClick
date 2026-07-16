# ThinkBeforeClick — FastAPI entrypoint
# Phase 1: initialize app, mount routers (health, analyze, report), CORS setup
from fastapi import FastAPI

from app.db.database import engine, Base
from app.api import health, analyze

# Creates scans/reports tables on startup if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ThinkBeforeClick API",
    description="Backend for the ThinkBeforeClick phishing detection tool.",
    version="0.1.0",
)

app.include_router(health.router, tags=["Health"])
app.include_router(analyze.router, tags=["Analyze"])