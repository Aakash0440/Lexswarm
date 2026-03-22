# tests/unit/test_escalation.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from intake.classifier import CaseClassifier
from regime.escalation_detector import EscalationDetector, HUMAN_ALERT_THRESHOLD
from intake.base import UrgencyLevel


class TestEscalationDetector:
    def setup_method(self):
        self.clf = CaseClassifier()
        self.det = EscalationDetector()

    def test_lockout_is_critical(self):
        case = self.clf.intake("Landlord locked me out tonight with nowhere to sleep")
        result = self.det.detect(case)
        assert result.urgency == UrgencyLevel.CRITICAL
        assert result.escalation_score >= 0.80

    def test_physical_threat_triggers_human_alert(self):
        case = self.clf.intake("My landlord is threatening me with violence")
        result = self.det.detect(case)
        assert result.requires_human is True
        assert result.escalation_score >= HUMAN_ALERT_THRESHOLD

    def test_routine_case_not_critical(self):
        case = self.clf.intake("I want to understand my rights as a tenant regarding rent increases")
        result = self.det.detect(case)
        assert result.urgency in (UrgencyLevel.LOW, UrgencyLevel.MEDIUM)

    def test_arrest_is_high_urgency(self):
        case = self.clf.intake("I was arrested by police without a warrant")
        result = self.det.detect(case)
        assert result.urgency.value >= UrgencyLevel.HIGH.value

    def test_response_time_critical_under_1h(self):
        case = self.clf.intake("Police are at my door right now to arrest me immediately")
        result = self.det.detect(case)
        assert result.recommended_response_hours <= 1.0

    def test_triggers_populated(self):
        case = self.clf.intake("Landlord locked me out and children are outside")
        result = self.det.detect(case)
        assert len(result.triggers) > 0

    def test_drift_detection(self):
        case = self.clf.intake("I have a general wage dispute with my employer")
        self.det.detect(case)
        case.raw_description = "My employer threatened me today and I may be arrested"
        result2 = self.det.detect(case)
        assert result2.drift_detected is True
