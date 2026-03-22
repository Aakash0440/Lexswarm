# api/models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CaseRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=5000,
        description="Describe your legal situation in any language")
    country_hint: Optional[str] = Field(None, description="ISO country code hint e.g. PK, US, IN")

    class Config:
        json_schema_extra = {"example": {
            "description": "My landlord locked me out tonight in Karachi. I have nowhere to sleep.",
            "country_hint": "PK"
        }}


class LegalRightResponse(BaseModel):
    right: str
    statute: str
    jurisdiction: str
    plain_english: str
    source_url: Optional[str] = ""


class ActionResponse(BaseModel):
    step_number: int
    action: str
    deadline: str
    how_to: str
    requires_human: bool


class DocumentResponse(BaseModel):
    doc_type: str
    title: str
    content: str
    citations: list[str] = []
    generated_at: datetime


class SimulationResponse(BaseModel):
    win_probability: float
    recommended_strategy: str
    best_argument: str
    judge_concerns: list[str] = []
    what_to_avoid: list[str] = []
    best_opening_statement: str = ""


class CaseResponse(BaseModel):
    case_id: str
    case_type: str
    urgency: str
    country: str
    language: str
    escalation_score: float
    requires_human_lawyer: bool
    legal_rights: list[LegalRightResponse] = []
    recommended_actions: list[ActionResponse] = []
    simulation: Optional[SimulationResponse] = None
    documents: list[DocumentResponse] = []
    human_volunteer_alerted: bool
    analyzed_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    cases_analyzed_today: int
    jurisdictions_covered: int
    languages_supported: int
    timestamp: datetime
