# intake/base.py
# Core data structures for LEXSWARM
# Every legal case flows through these dataclasses

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class CaseType(Enum):
    CRIMINAL     = "criminal"
    CIVIL        = "civil"
    FAMILY       = "family"
    LABOR        = "labor"
    IMMIGRATION  = "immigration"
    HOUSING      = "housing"
    CONSUMER     = "consumer"
    HUMAN_RIGHTS = "human_rights"
    UNKNOWN      = "unknown"


class UrgencyLevel(Enum):
    LOW      = 1   # weeks to respond
    MEDIUM   = 2   # days to respond
    HIGH     = 3   # hours to respond
    CRITICAL = 4   # immediate — arrest, eviction, deportation tonight


class CaseStatus(Enum):
    INTAKE      = "intake"
    ANALYZING   = "analyzing"
    ACTION_PLAN = "action_plan"
    ESCALATED   = "escalated"   # human volunteer alerted
    RESOLVED    = "resolved"
    CLOSED      = "closed"


@dataclass
class LegalCase:
    """Core case object — created at intake, updated throughout pipeline."""
    case_id: str
    raw_description: str          # user's own words
    language: str                 # detected language code (e.g. "en", "ur", "id")
    jurisdiction: str             # detected jurisdiction (e.g. "PK-SD", "US-NY", "GB-ENG")
    country: str                  # ISO 3166-1 alpha-2
    case_type: CaseType
    urgency: UrgencyLevel
    status: CaseStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Enriched during pipeline
    translated_description: str = ""
    key_facts: list = field(default_factory=list)
    relevant_statutes: list = field(default_factory=list)
    legal_rights: list = field(default_factory=list)
    recommended_actions: list = field(default_factory=list)
    generated_documents: list = field(default_factory=list)
    simulation_result: dict = field(default_factory=dict)
    escalation_score: float = 0.0
    human_volunteer_alerted: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class LegalDocument:
    """A generated legal document — demand letter, court form, etc."""
    doc_type: str          # "demand_letter" | "court_complaint" | "rights_notice" | "appeal"
    title: str
    content: str           # full document text
    jurisdiction: str
    language: str
    citations: list = field(default_factory=list)   # statutes cited
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    downloadable: bool = True


@dataclass
class LegalRight:
    """A specific legal right relevant to the case."""
    right: str             # plain language description
    statute: str           # the actual law e.g. "Section 14, Tenancy Act 2009"
    jurisdiction: str
    source_url: str = ""
    plain_english: str = ""   # one-sentence explanation for non-lawyers


@dataclass
class RecommendedAction:
    """A concrete step the user should take."""
    step_number: int
    action: str            # what to do
    deadline: str          # when to do it ("within 24 hours", "before court date")
    how_to: str            # detailed instructions
    urgency: UrgencyLevel
    requires_human: bool = False   # does this need a real lawyer?
