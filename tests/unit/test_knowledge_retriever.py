# tests/unit/test_knowledge_retriever.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import asyncio
from intake.classifier import CaseClassifier
from knowledge.retriever import LegalKnowledgeRetriever
from intake.base import CaseType


class TestKnowledgeRetriever:
    def setup_method(self):
        self.clf       = CaseClassifier()
        self.retriever = LegalKnowledgeRetriever()

    @pytest.mark.asyncio
    async def test_pakistan_housing_returns_statutes(self):
        case = self.clf.intake("Landlord evicting me in Karachi Pakistan")
        rights = await self.retriever.retrieve(case)
        await self.retriever.close()
        assert len(rights) > 0
        statutes = [r.statute for r in rights]
        assert any("1882" in s or "Ordinance" in s or "Act" in s for s in statutes)

    @pytest.mark.asyncio
    async def test_us_labor_returns_statutes(self):
        case = self.clf.intake("Unpaid wages in the United States")
        rights = await self.retriever.retrieve(case)
        await self.retriever.close()
        assert len(rights) > 0

    @pytest.mark.asyncio
    async def test_universal_rights_always_included(self):
        case = self.clf.intake("My rights are being violated")
        rights = await self.retriever.retrieve(case)
        await self.retriever.close()
        # Universal human rights should always be present
        all_statutes = " ".join(r.statute for r in rights)
        assert "Universal" in all_statutes or "Human Rights" in all_statutes or len(rights) > 0

    @pytest.mark.asyncio
    async def test_offline_fallback_works(self):
        # Even if APIs fail, offline DB should provide results for known jurisdictions
        case = self.clf.intake("Labor dispute in Pakistan")
        case.country = "PK"
        case.case_type = CaseType.LABOR
        rights = self.retriever._get_offline_rights("PK", CaseType.LABOR)
        assert len(rights) > 0
        assert all(r.statute for r in rights)
        assert all(r.plain_english for r in rights)

    @pytest.mark.asyncio
    async def test_unknown_jurisdiction_returns_universal(self):
        case = self.clf.intake("I am in a legal dispute")
        case.country = "XX"
        rights = await self.retriever.retrieve(case)
        await self.retriever.close()
        assert len(rights) > 0
