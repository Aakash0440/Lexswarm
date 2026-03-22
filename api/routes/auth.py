# api/routes/auth.py
# Supabase auth integration for LEXSWARM
# Handles JWT verification + case persistence
# pip install supabase

import os
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from supabase import create_client, Client
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")   # service key — server only
SUPABASE_ANON = os.getenv("SUPABASE_ANON_KEY")     # anon key — safe for frontend

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Auth helpers ──────────────────────────────────────────────────────────────

def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Extract and verify Supabase JWT from Authorization header.
    Returns user dict if valid, None if no token (anonymous allowed).
    Raises 401 if token is present but invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        user = supabase.auth.get_user(token)
        return user.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_user(user=Depends(get_current_user)) -> dict:
    """Use this dependency on routes that require login."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


# ── Case persistence ──────────────────────────────────────────────────────────

class SaveCaseRequest(BaseModel):
    case_ref: str
    case_type: str
    urgency: str
    country: str
    language: str
    description: str
    legal_rights: list
    action_plan: list
    documents: list
    simulation: dict
    win_probability: int
    lawyer_alerted: bool
    flags: dict


@router.post("/cases/save")
async def save_case(
    payload: SaveCaseRequest,
    user=Depends(require_user),
):
    """
    Save a completed case to the user's history.
    Called automatically after pipeline completes if user is logged in.
    """
    try:
        result = supabase.table("cases").insert({
            "user_id":        user.id,
            "case_ref":       payload.case_ref,
            "case_type":      payload.case_type,
            "urgency":        payload.urgency,
            "country":        payload.country,
            "language":       payload.language,
            "description":    payload.description,
            "legal_rights":   payload.legal_rights,
            "action_plan":    payload.action_plan,
            "documents":      payload.documents,
            "simulation":     payload.simulation,
            "win_probability":payload.win_probability,
            "lawyer_alerted": payload.lawyer_alerted,
            "flags":          payload.flags,
        }).execute()
        return {"saved": True, "id": result.data[0]["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cases")
async def get_user_cases(user=Depends(require_user)):
    """Return all cases for the logged-in user, newest first."""
    try:
        result = (
            supabase.table("cases")
            .select("*")
            .eq("user_id", user.id)
            .order("created_at", desc=True)
            .execute()
        )
        return {"cases": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cases/{case_ref}")
async def get_case(case_ref: str, user=Depends(require_user)):
    """Return a specific case by reference ID."""
    try:
        result = (
            supabase.table("cases")
            .select("*")
            .eq("user_id", user.id)
            .eq("case_ref", case_ref)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Case not found")
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
