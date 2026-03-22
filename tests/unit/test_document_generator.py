# tests/unit/test_document_generator.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import asyncio
from intake.classifier import CaseClassifier
from agent.document_generator import LegalDocumentGenerator
from knowledge.retriever import LegalKnowledgeRetriever
from intake.base import UrgencyLevel, CaseType


class TestDocumentGenerator:
    def setup_method(self):
        self.clf = CaseClassifier()
        self.gen = LegalDocumentGenerator()

    @pytest.mark.asyncio
    async def test_rights_notice_always_generated(self):
        case = self.clf.intake("My landlord is evicting me in Karachi")
        retriever = LegalKnowledgeRetriever()
        case.legal_rights = await retriever.retrieve(case)
        await retriever.close()
        case.recommended_actions = self.gen.build_action_plan(case)
        docs = self.gen.generate_all_documents(case)
        types = [d.doc_type for d in docs]
        assert "rights_notice" in types

    @pytest.mark.asyncio
    async def test_demand_letter_always_generated(self):
        case = self.clf.intake("My employer has not paid wages in Indonesia")
        retriever = LegalKnowledgeRetriever()
        case.legal_rights = await retriever.retrieve(case)
        await retriever.close()
        case.recommended_actions = self.gen.build_action_plan(case)
        docs = self.gen.generate_all_documents(case)
        types = [d.doc_type for d in docs]
        assert "demand_letter" in types

    @pytest.mark.asyncio
    async def test_court_complaint_for_high_urgency(self):
        case = self.clf.intake("Landlord locked me out tonight in the US")
        case.urgency = UrgencyLevel.CRITICAL
        retriever = LegalKnowledgeRetriever()
        case.legal_rights = await retriever.retrieve(case)
        await retriever.close()
        case.recommended_actions = self.gen.build_action_plan(case)
        docs = self.gen.generate_all_documents(case)
        types = [d.doc_type for d in docs]
        assert "court_complaint" in types

    def test_demand_letter_has_jurisdiction(self):
        case = self.clf.intake("My landlord is evicting me in London UK")
        case.legal_rights = []
        doc = self.gen.generate_demand_letter(case)
        assert doc is not None
        assert len(doc.content) > 100

    def test_action_plan_has_steps(self):
        case = self.clf.intake("I was wrongfully terminated from my job")
        case.legal_rights = []
        actions = self.gen.build_action_plan(case)
        assert len(actions) >= 3
        assert all(a.step_number > 0 for a in actions)
        assert all(len(a.action) > 5 for a in actions)

    def test_documents_include_statute_citations(self):
        from intake.base import LegalRight
        case = self.clf.intake("My landlord locked me out in Pakistan")
        case.legal_rights = [
            LegalRight(
                right="Protection against illegal lockout",
                statute="Transfer of Property Act 1882, Section 108",
                jurisdiction="PK",
                plain_english="Changing locks without court order is illegal.",
            )
        ]
        doc = self.gen.generate_demand_letter(case)
        assert "Transfer of Property Act" in doc.content or len(doc.citations) > 0
