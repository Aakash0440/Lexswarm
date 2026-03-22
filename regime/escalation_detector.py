# regime/escalation_detector.py
# FRAMEWORM-SHIFT applied to legal cases
# Detects when a case is escalating from routine -> urgent -> crisis
# Triggers human volunteer alert when threshold crossed
#
# Instead of market regime drift, we detect LEGAL SITUATION DRIFT:
#   routine dispute -> imminent court date -> arrest risk -> deportation tonight

from dataclasses import dataclass
from datetime import datetime, timezone
from intake.base import UrgencyLevel, CaseType


@dataclass
class EscalationResult:
    escalation_score: float       # 0.0 = routine, 1.0 = maximum crisis
    urgency: UrgencyLevel
    triggers: list[str]           # what caused the escalation
    requires_human: bool          # should we alert a volunteer lawyer?
    recommended_response_hours: float   # how many hours before action needed
    drift_detected: bool          # has situation worsened since last check?


# ── Escalation signal patterns ─────────────────────────────────────────────────

ESCALATION_SIGNALS = {
    # Physical safety threats — always CRITICAL
    "physical_threat": {
        "keywords": ["threatened", "violence", "assault", "weapon", "hurt me",
                     "beat", "تشدد", "خطرہ", "ancaman", "kekerasan"],
        "score": 0.95,
        "urgency": UrgencyLevel.CRITICAL,
    },
    # Imminent arrest or detention
    "imminent_arrest": {
        "keywords": ["police at my door", "being arrested", "warrant", "raid",
                     "پولیس آ گئی", "گرفتار ہو رہا", "polisi datang", "ditangkap"],
        "score": 0.90,
        "urgency": UrgencyLevel.CRITICAL,
    },
    # Active eviction — happening now
    "active_eviction": {
        "keywords": ["locked out", "locks changed", "belongings outside",
                     "no place to sleep", "تالہ لگا دیا", "dikunci", "diusir"],
        "score": 0.90,
        "urgency": UrgencyLevel.CRITICAL,
    },
    # Deportation or immigration detention
    "deportation_risk": {
        "keywords": ["deportation order", "immigration detention", "ICE",
                     "removed from country", "ملک بدر", "deportasi", "ditahan imigrasi"],
        "score": 0.90,
        "urgency": UrgencyLevel.CRITICAL,
    },
    # Court date within 48 hours
    "imminent_court": {
        "keywords": ["court tomorrow", "hearing tomorrow", "court today",
                     "کل عدالت", "sidang besok", "pengadilan hari ini"],
        "score": 0.75,
        "urgency": UrgencyLevel.HIGH,
    },
    # Children at risk
    "child_welfare": {
        "keywords": ["child removed", "custody battle", "CPS", "children at risk",
                     "بچہ لے گئے", "hak asuh anak", "anak terancam"],
        "score": 0.80,
        "urgency": UrgencyLevel.HIGH,
    },
    # Unpaid wages — financial crisis
    "wage_theft": {
        "keywords": ["not paid", "months of salary", "unpaid wages",
                     "تنخواہ نہیں ملی", "upah tidak dibayar", "gaji belum dibayar"],
        "score": 0.55,
        "urgency": UrgencyLevel.MEDIUM,
    },
    # Employer threats
    "employer_threat": {
        "keywords": ["threatened by employer", "fired illegally", "blacklisted",
                     "مالک نے دھمکی دی", "diancam majikan", "dipecat tidak adil"],
        "score": 0.60,
        "urgency": UrgencyLevel.MEDIUM,
    },
}

# Case types that almost always require human lawyer review
HIGH_RISK_CASE_TYPES = {
    CaseType.CRIMINAL,
    CaseType.IMMIGRATION,
    CaseType.FAMILY,   # especially custody
}

# Score thresholds
HUMAN_ALERT_THRESHOLD = 0.70   # alert volunteer lawyer above this
CRITICAL_THRESHOLD    = 0.85   # maximum emergency response


class EscalationDetector:
    """
    FRAMEWORM-SHIFT for legal case escalation detection.

    Monitors a case description for signals that the situation is worsening
    and requires immediate human intervention.

    Same statistical approach as QUANTSHIFT's regime detector but applied
    to legal crisis signals instead of market volatility patterns.
    """

    def __init__(self):
        self.case_history: dict[str, list[float]] = {}   # case_id -> score history

    def detect(self, case) -> EscalationResult:
        """
        Analyze case for escalation signals.
        Returns EscalationResult with score, urgency, and human alert flag.
        """
        text = (case.raw_description + " " +
                case.translated_description + " " +
                " ".join(case.key_facts)).lower()

        total_score = 0.0
        triggers = []
        max_urgency = case.urgency

        for signal_name, signal in ESCALATION_SIGNALS.items():
            matched = any(kw in text for kw in signal["keywords"])
            if matched:
                total_score = max(total_score, signal["score"])
                triggers.append(signal_name.replace("_", " "))
                if signal["urgency"].value > max_urgency.value:
                    max_urgency = signal["urgency"]

        # Case type modifier
        if case.case_type in HIGH_RISK_CASE_TYPES:
            total_score = min(total_score + 0.15, 1.0)
            if CaseType.CRIMINAL == case.case_type:
                triggers.append("criminal case — always high risk")

        # Drift detection — has score worsened since last check?
        drift_detected = False
        history = self.case_history.get(case.case_id, [])
        if history and total_score > history[-1] + 0.10:
            drift_detected = True
            triggers.append(f"situation worsening (score: {history[-1]:.2f} -> {total_score:.2f})")

        # Update history
        history.append(total_score)
        self.case_history[case.case_id] = history[-10:]   # keep last 10

        requires_human = (
            total_score >= HUMAN_ALERT_THRESHOLD or
            max_urgency == UrgencyLevel.CRITICAL or
            case.case_type in HIGH_RISK_CASE_TYPES
        )

        # Response time recommendation
        response_hours = {
            UrgencyLevel.CRITICAL: 0.5,    # 30 minutes
            UrgencyLevel.HIGH:     4.0,    # 4 hours
            UrgencyLevel.MEDIUM:   24.0,   # 1 day
            UrgencyLevel.LOW:      72.0,   # 3 days
        }[max_urgency]

        if total_score >= CRITICAL_THRESHOLD:
            response_hours = 0.25   # 15 minutes — maximum emergency

        print(f"[EscalationDetector] Case {case.case_id}: score={total_score:.2f} "
              f"urgency={max_urgency.name} human={requires_human} drift={drift_detected}")

        return EscalationResult(
            escalation_score=round(total_score, 3),
            urgency=max_urgency,
            triggers=triggers,
            requires_human=requires_human,
            recommended_response_hours=response_hours,
            drift_detected=drift_detected,
        )
