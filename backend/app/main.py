# ThinkBeforeClick — FastAPI entrypoint
# Phase 1: initialize app, mount routers (health, analyze, report), CORS setup
from fastapi import FastAPI

from app.db.database import engine, Base
from app.api import health, analyze
from fastapi.middleware.cors import CORSMiddleware

# Creates scans/reports tables on startup if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ThinkBeforeClick API",
    description="Backend for the ThinkBeforeClick phishing detection tool.",
    version="0.1.0",
)

# --- CORS: allows the webapp (served on a different local port) to call this API ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # fine for local dev; tighten to your real domain(s) before deploying
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(analyze.router, tags=["Analyze"])