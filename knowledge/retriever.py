# knowledge/retriever.py
# Loads all statutes from config/jurisdictions.yaml automatically
# 10 countries x 10 case types = 100 statute sets
# No hardcoded statute lists — add new countries just by editing the YAML

import httpx
import yaml
import os
from dataclasses import dataclass
from intake.base import CaseType, LegalRight

@dataclass
class StatuteResult:
    title: str
    text: str
    citation: str
    source: str
    url: str
    jurisdiction: str
    relevance_score: float

COURTLISTENER_BASE = "https://www.courtlistener.com/api/rest/v3"

CASE_TYPE_MAP = {
    "housing":                   CaseType.HOUSING,
    "labor":                     CaseType.LABOR,
    "criminal":                  CaseType.CRIMINAL,
    "family":                    CaseType.FAMILY,
    "immigration":               CaseType.IMMIGRATION,
    "consumer":                  CaseType.CONSUMER,
    "civil":                     CaseType.CIVIL,
    "human_rights":              CaseType.HUMAN_RIGHTS,
    "debt":                      CaseType.CIVIL,
    "employment_discrimination":  CaseType.LABOR,
}

UNIVERSAL_RIGHTS = {
    CaseType.LABOR: [
        LegalRight(right="Right to just and favourable conditions of work",
                   statute="Universal Declaration of Human Rights, Article 23",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to just conditions of work, equal pay, and protection against unemployment."),
        LegalRight(right="Right to fair pay and reasonable working hours",
                   statute="Universal Declaration of Human Rights, Article 24",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to fair remuneration and reasonable working hours. Unpaid overtime violates this right."),
        LegalRight(right="Protection of wages against unlawful withholding",
                   statute="ILO Convention No. 95 — Protection of Wages (1949)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Wages must be paid in full, regularly, and directly to the worker."),
        LegalRight(right="Protection against retaliatory dismissal",
                   statute="ILO Convention No. 158 — Termination of Employment (1982)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Termination for raising a wage complaint is unlawful retaliation under international labour standards."),
    ],
    CaseType.HOUSING: [
        LegalRight(right="Right to adequate housing",
                   statute="ICESCR Article 11",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to adequate housing. Forced eviction without legal notice violates international law."),
        LegalRight(right="Protection from arbitrary deprivation of property",
                   statute="Universal Declaration of Human Rights, Article 17",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="No one may be deprived of their home without lawful due process and a court order."),
    ],
    CaseType.CRIMINAL: [
        LegalRight(right="Prohibition of arbitrary detention",
                   statute="Universal Declaration of Human Rights, Article 9",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="No one may be arrested or detained arbitrarily without legal basis."),
        LegalRight(right="Right to be informed of charges",
                   statute="ICCPR Article 9(2)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Anyone arrested must be informed promptly of charges in a language they understand."),
        LegalRight(right="Right to legal representation",
                   statute="ICCPR Article 14(3)(d)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Every accused person has the right to legal representation. If they cannot afford a lawyer, one must be provided."),
    ],
    CaseType.FAMILY: [
        LegalRight(right="Protection of the family unit",
                   statute="Universal Declaration of Human Rights, Article 16(3)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="The family is a fundamental unit of society entitled to protection by the State."),
        LegalRight(right="Best interests of the child",
                   statute="UN Convention on the Rights of the Child, Article 3",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="In all decisions concerning children, the best interests of the child must be the primary consideration."),
    ],
    CaseType.IMMIGRATION: [
        LegalRight(right="Right to seek asylum",
                   statute="Universal Declaration of Human Rights, Article 14",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to seek and enjoy asylum from persecution."),
        LegalRight(right="Non-refoulement protection",
                   statute="1951 Refugee Convention, Article 33",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="No person may be returned to a country where they face persecution or serious harm."),
    ],
    CaseType.CONSUMER: [
        LegalRight(right="Right to effective legal remedy",
                   statute="Universal Declaration of Human Rights, Article 8",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to an effective remedy by a competent tribunal."),
        LegalRight(right="UN Consumer Protection Guidelines",
                   statute="UN Guidelines for Consumer Protection (2015)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Consumers have rights to safety, information, choice, and redress under UN guidelines."),
    ],
    CaseType.CIVIL: [
        LegalRight(right="Right to effective legal remedy",
                   statute="Universal Declaration of Human Rights, Article 8",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to an effective remedy by a competent national tribunal."),
        LegalRight(right="Right to fair trial",
                   statute="Universal Declaration of Human Rights, Article 10",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone is entitled to a fair and public hearing by an independent tribunal."),
    ],
    CaseType.HUMAN_RIGHTS: [
        LegalRight(right="Prohibition of torture",
                   statute="UN Convention Against Torture, Article 1",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="No one may be tortured or subjected to cruel or degrading treatment under any circumstances."),
        LegalRight(right="Right to equality before the law",
                   statute="Universal Declaration of Human Rights, Article 7",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="All people are equal before the law and entitled to equal protection without discrimination."),
    ],
    CaseType.UNKNOWN: [
        LegalRight(right="Right to equality before the law",
                   statute="Universal Declaration of Human Rights, Article 7",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="All people are equal before the law and entitled to equal protection."),
        LegalRight(right="Right to effective legal remedy",
                   statute="Universal Declaration of Human Rights, Article 8",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to an effective remedy by a competent national tribunal."),
    ],
}


def _load_yaml_statutes() -> dict:
    """
    Load all statutes from config/jurisdictions.yaml at startup.
    Returns dict keyed by (country_code, case_type_string).
    Add new countries by editing the YAML only — no code changes needed.
    """
    yaml_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "jurisdictions.yaml"
    )
    db = {}
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for country_name, country_data in data.items():
            code = country_data.get("code", "XX")
            for case_type_str, rights_list in country_data.get("statutes", {}).items():
                rights = [
                    LegalRight(
                        right=r.get("right", ""),
                        statute=r.get("statute", ""),
                        jurisdiction=code,
                        source_url=r.get("source_url", ""),
                        plain_english=r.get("plain_english", ""),
                    )
                    for r in rights_list
                ]
                db[(code, case_type_str)] = rights

        print(f"[Retriever] Loaded {len(db)} statute sets from jurisdictions.yaml "
              f"({len(set(k[0] for k in db))} countries × {len(set(k[1] for k in db))} case types)")

    except FileNotFoundError:
        print("[Retriever] WARNING: jurisdictions.yaml not found")
    except Exception as e:
        print(f"[Retriever] ERROR loading yaml: {e}")
    return db


# Load once at startup — shared across all requests
_STATUTE_DB = _load_yaml_statutes()

ENUM_TO_STR = {
    CaseType.HOUSING:     "housing",
    CaseType.LABOR:       "labor",
    CaseType.CRIMINAL:    "criminal",
    CaseType.FAMILY:      "family",
    CaseType.IMMIGRATION: "immigration",
    CaseType.CONSUMER:    "consumer",
    CaseType.CIVIL:       "civil",
    CaseType.HUMAN_RIGHTS:"human_rights",
    CaseType.UNKNOWN:     "general",
}


class LegalKnowledgeRetriever:
    """
    Retrieves statutes for a given case from 100-case YAML database.
    Add new countries/case types by editing jurisdictions.yaml only.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15)

    async def _query_courtlistener(self, query: str, jurisdiction: str) -> list[LegalRight]:
        results = []
        try:
            resp = await self.client.get(f"{COURTLISTENER_BASE}/search/",
                params={"q": query, "type": "o", "order_by": "score desc", "stat_Precedential": "on"})
            for hit in resp.json().get("results", [])[:2]:
                results.append(LegalRight(
                    right=hit.get("caseName", ""),
                    statute=hit.get("citation", ""),
                    jurisdiction=jurisdiction,
                    source_url=f"https://www.courtlistener.com{hit.get('absolute_url', '')}",
                    plain_english=hit.get("snippet", "")[:200],
                ))
        except Exception as e:
            print(f"[Retriever] CourtListener failed: {e}")
        return results

    def _get_local_rights(self, country: str, case_type: CaseType) -> list[LegalRight]:
        ct_str = ENUM_TO_STR.get(case_type, "general")

        # Try exact match
        rights = _STATUTE_DB.get((country, ct_str), [])
        if rights:
            return rights

        # Also try debt and employment_discrimination for CIVIL/LABOR
        if case_type == CaseType.CIVIL:
            rights = _STATUTE_DB.get((country, "debt"), [])
        elif case_type == CaseType.LABOR:
            rights = _STATUTE_DB.get((country, "employment_discrimination"), [])
            base = _STATUTE_DB.get((country, "labor"), [])
            return base + rights

        # Parent jurisdiction fallback
        if not rights and "-" in country:
            parent = country.split("-")[0]
            rights = _STATUTE_DB.get((parent, ct_str), [])

        return rights

    async def retrieve(self, case) -> list[LegalRight]:
        rights = []

        # 1. Local statutes from YAML
        local = self._get_local_rights(case.country, case.case_type)
        rights.extend(local)

        # 2. Correct international law for this case type
        intl = UNIVERSAL_RIGHTS.get(case.case_type, UNIVERSAL_RIGHTS[CaseType.UNKNOWN])
        needed = max(0, 4 - len(rights))
        rights.extend(intl[:needed])

        # 3. Live CourtListener for US cases
        if case.country == "US" and len(rights) < 5:
            query = f"{ENUM_TO_STR.get(case.case_type, '')} {' '.join(case.key_facts[:2])}"
            rights.extend(await self._query_courtlistener(query, case.jurisdiction))

        ct_str = ENUM_TO_STR.get(case.case_type, "?")
        print(f"[Retriever] {len(rights)} statutes → {case.country}/{ct_str} "
              f"({len(local)} local + {min(len(intl), needed)} intl)")
        return rights

    async def close(self):
        await self.client.aclose()