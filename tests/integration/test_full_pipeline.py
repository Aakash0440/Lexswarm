# tests/integration/test_full_pipeline.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import asyncio
from intake.classifier import CaseClassifier
from knowledge.retriever import LegalKnowledgeRetriever
from regime.escalation_detector import EscalationDetector
from simulation.courtroom_swarm import CourtroomSwarm
from agent.document_generator import LegalDocumentGenerator
from intake.base import UrgencyLevel, CaseType


class TestFullPipeline:
    """End-to-end pipeline tests — no API keys required."""

    def setup_method(self):
        self.clf       = CaseClassifier()
        self.detector  = EscalationDetector()
        self.swarm     = CourtroomSwarm(n_agents_per_type=20)
        self.generator = LegalDocumentGenerator()

    @pytest.mark.asyncio
    async def test_pakistan_housing_case_full_pipeline(self):
        """Full pipeline: Karachi lockout case."""
        description = "My landlord changed the locks tonight in Karachi. I have three children."

        # Classify
        case = self.clf.intake(description)
        assert case.case_type == CaseType.HOUSING
        assert case.country == "PK"

        # Escalation
        escalation = self.detector.detect(case)
        assert escalation.urgency == UrgencyLevel.CRITICAL
        assert escalation.requires_human is True
        case.urgency = escalation.urgency

        # Knowledge retrieval
        retriever = LegalKnowledgeRetriever()
        case.legal_rights = await retriever.retrieve(case)
        assert len(case.legal_rights) > 0
        await retriever.close()

        # Simulation
        sim = self.swarm.simulate(case, mock=True)
        assert sim.overall_win_probability > 0

        # Documents
        case.recommended_actions = self.generator.build_action_plan(case)
        docs = self.generator.generate_all_documents(case)
        assert len(docs) >= 2   # rights notice + demand letter at minimum

        # Check demand letter has statute citations
        demand_letter = next((d for d in docs if d.doc_type == "demand_letter"), None)
        assert demand_letter is not None
        assert len(demand_letter.citations) > 0

    @pytest.mark.asyncio
    async def test_us_labor_case_full_pipeline(self):
        """Full pipeline: US unpaid wages case."""
        description = "My employer has not paid my wages for 2 months in New York"

        case = self.clf.intake(description)
        assert case.case_type == CaseType.LABOR
        assert case.country == "US"

        escalation = self.detector.detect(case)
        case.urgency = escalation.urgency

        retriever = LegalKnowledgeRetriever()
        case.legal_rights = await retriever.retrieve(case)
        await retriever.close()

        assert any("Fair Labor" in r.statute or "Wages" in r.statute or "Labor" in r.statute
                   for r in case.legal_rights)

    @pytest.mark.asyncio
    async def test_critical_case_human_alert_flag(self):
        """Critical cases must set requires_human=True."""
        description = "Police arrested me right now without showing warrant. I need help immediately."

        case = self.clf.intake(description)
        escalation = self.detector.detect(case)
        assert escalation.requires_human is True
        assert escalation.recommended_response_hours <= 2.0

    @pytest.mark.asyncio
    async def test_document_generation_all_types(self):
        """High urgency case should generate 3 document types."""
        description = "Landlord is locking me out tonight. Court hearing is tomorrow."

        case = self.clf.intake(description)
        escalation = self.detector.detect(case)
        case.urgency = escalation.urgency

        retriever = LegalKnowledgeRetriever()
        case.legal_rights = await retriever.retrieve(case)
        await retriever.close()

        case.recommended_actions = self.generator.build_action_plan(case)
        docs = self.generator.generate_all_documents(case)

        doc_types = {d.doc_type for d in docs}
        assert "rights_notice" in doc_types
        assert "demand_letter" in doc_types

    @pytest.mark.asyncio
    async def test_multilingual_urdu_case(self):
        """Urdu input should still produce a valid case."""
        description = "میرے مالک مکان نے آج رات تالہ بدل دیا۔ کراچی میں ہوں۔"
        case = self.clf.intake(description)
        assert case is not None
        assert case.case_id is not None
