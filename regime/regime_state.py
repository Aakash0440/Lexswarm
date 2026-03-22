# regime/regime_state.py
# Tracks escalation history for each case over time
# Detects if situation is worsening (drift detection applied to legal urgency)

from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import deque
from intake.base import UrgencyLevel


@dataclass
class EscalationEvent:
    timestamp: datetime
    score: float
    urgency: UrgencyLevel
    triggers: list[str]
    human_alerted: bool = False


class LegalRegimeState:
    """
    Tracks escalation history for a legal case over time.
    Detects drift — is the situation getting worse or better?

    Analogous to QUANTSHIFT's RegimeState but for legal urgency levels.
    """

    def __init__(self, case_id: str):
        self.case_id     = case_id
        self.history: deque = deque(maxlen=50)
        self.peak_score  = 0.0
        self.alert_count = 0

    def record(self, score: float, urgency: UrgencyLevel, triggers: list[str]) -> bool:
        """
        Record new escalation check. Returns True if situation is worsening.
        """
        event = EscalationEvent(
            timestamp=datetime.now(timezone.utc),
            score=score,
            urgency=urgency,
            triggers=triggers,
        )
        self.history.append(event)
        self.peak_score = max(self.peak_score, score)

        # Drift detection: is score trending up?
        if len(self.history) >= 3:
            recent = [e.score for e in list(self.history)[-3:]]
            return recent[-1] > recent[0] + 0.10   # worsening by 10%+
        return False

    def is_resolved(self) -> bool:
        """Has the situation been de-escalating for the last 3 checks?"""
        if len(self.history) < 3:
            return False
        recent = [e.score for e in list(self.history)[-3:]]
        return recent[-1] < 0.30 and all(r < 0.40 for r in recent)

    def trend(self) -> str:
        """Returns 'escalating' | 'stable' | 'de-escalating'"""
        if len(self.history) < 2:
            return "stable"
        scores = [e.score for e in list(self.history)[-5:]]
        if scores[-1] > scores[0] + 0.10:
            return "escalating"
        if scores[-1] < scores[0] - 0.10:
            return "de-escalating"
        return "stable"

    def summary(self) -> dict:
        return {
            "case_id":    self.case_id,
            "checks":     len(self.history),
            "peak_score": round(self.peak_score, 3),
            "trend":      self.trend(),
            "resolved":   self.is_resolved(),
            "alerts_sent": self.alert_count,
        }
