# tests/unit/test_classifier.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from intake.classifier import CaseClassifier
from intake.base import CaseType, UrgencyLevel


class TestCaseClassifier:
    def setup_method(self):
        self.clf = CaseClassifier()

    def test_housing_classification(self):
        text = "My landlord locked me out and threw my belongings outside"
        case = self.clf.intake(text)
        assert case.case_type == CaseType.HOUSING

    def test_labor_classification(self):
        text = "My employer has not paid my salary for 3 months and fired me illegally"
        case = self.clf.intake(text)
        assert case.case_type == CaseType.LABOR

    def test_criminal_classification(self):
        text = "Police arrested me without a warrant and I have been charged"
        case = self.clf.intake(text)
        assert case.case_type == CaseType.CRIMINAL

    def test_immigration_classification(self):
        text = "I received a deportation order and need asylum protection"
        case = self.clf.intake(text)
        assert case.case_type == CaseType.IMMIGRATION

    def test_critical_urgency(self):
        text = "My landlord locked me out tonight and I have nowhere to sleep right now"
        case = self.clf.intake(text)
        assert case.urgency == UrgencyLevel.CRITICAL

    def test_pakistan_jurisdiction(self):
        text = "My landlord evicted me in Karachi Pakistan"
        case = self.clf.intake(text)
        assert case.country == "PK"

    def test_us_jurisdiction(self):
        text = "My employer violated my rights under federal law in the United States"
        case = self.clf.intake(text)
        assert case.country == "US"

    def test_case_id_generated(self):
        text = "I have a labor dispute with my employer"
        case = self.clf.intake(text)
        assert case.case_id is not None
        assert len(case.case_id) > 0

    def test_key_facts_extracted(self):
        text = "My landlord locked me out. I have three children. We have nowhere to go tonight."
        case = self.clf.intake(text)
        assert len(case.key_facts) > 0
