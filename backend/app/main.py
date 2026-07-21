# ThinkBeforeClick — FastAPI entrypoint
# Phase 1: initialize app, mount routers (health, analyze, report), CORS setup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine, Base
from app.api import health, analyze

# Creates scans/reports tables on startup if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ThinkBeforeClick API",
    description="Backend for the ThinkBeforeClick phishing detection tool.",
    version="0.1.0",
)

# --- CORS Setup ---
origins = [
    # Custom Domain
    "https://thinkbeforeclick.me",
    "https://www.thinkbeforeclick.me",
    "http://thinkbeforeclick.me",       # handles http -> https redirects smoothly
    "http://www.thinkbeforeclick.me",
    
    # Render Default URLs
    "https://thinkbeforeclick-frontend.onrender.com",
    
    # Local Development
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://localhost:3000",            # common default if using React/Vite/Next locally
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(analyze.router, tags=["Analyze"])