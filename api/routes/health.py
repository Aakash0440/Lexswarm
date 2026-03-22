# api/routes/health.py
from fastapi import APIRouter
from api.models import HealthResponse
from datetime import datetime, timezone

router = APIRouter()
_start_time = datetime.now(timezone.utc)
_cases_today = 0

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        cases_analyzed_today=_cases_today,
        jurisdictions_covered=100,
        languages_supported=100,
        timestamp=datetime.now(timezone.utc),
    )

@router.get("/ping", tags=["System"])
async def ping():
    return {"status": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}
