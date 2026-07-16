# Phase 1: GET /health -> simple {"status": "ok"} check
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}