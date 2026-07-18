# Phase 1: app settings, env var loading (API keys, DB path, CORS origins)
# Phase 1 scaffold, implemented now for Phase 4 (Safe Browsing API key needs real env loading)
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SAFE_BROWSING_API_KEY: str = os.getenv("SAFE_BROWSING_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./thinkbeforeclick.db")


settings = Settings()