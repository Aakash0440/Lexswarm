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

# How many local statutes we expect per case type before flagging low coverage
EXPECTED_LOCAL_STATUTES = 3

CASE_TYPE_MAP = {
    "housing":                    CaseType.HOUSING,
    "labor":                      CaseType.LABOR,
    "criminal":                   CaseType.CRIMINAL,
    "family":                     CaseType.FAMILY,
    "immigration":                CaseType.IMMIGRATION,
    "consumer":                   CaseType.CONSUMER,
    "civil":                      CaseType.CIVIL,
    "human_rights":               CaseType.HUMAN_RIGHTS,
    "debt":                       CaseType.CIVIL,
    "employment_discrimination":  CaseType.LABOR,
}

# Rights that apply when the person is stateless or their jurisdiction has no domestic
# statute coverage — bypasses local YAML entirely for these individuals
STATELESS_RIGHTS = {
    CaseType.CRIMINAL: [
        LegalRight(
            right="Prohibition of arbitrary detention of children",
            statute="UN Convention on the Rights of the Child, Article 37",
            jurisdiction="UNIVERSAL", source_url="",
            plain_english="No child may be subjected to arbitrary detention. Detention must be a last resort "
                          "and for the shortest possible time. Bangladesh ratified CRC in 1990.",
        ),
        LegalRight(
            right="Right of refugee children to protection",
            statute="UN Convention on the Rights of the Child, Article 22",
            jurisdiction="UNIVERSAL", source_url="",
            plain_english="Children seeking refugee status are entitled to special protection. States must "
                          "cooperate with UNHCR and other agencies to protect such children.",
        ),
        LegalRight(
            right="Non-refoulement — protection from return to persecution",
            statute="Customary International Law / UNHCR Statute Article 33",
            jurisdiction="UNIVERSAL", source_url="",
            plain_english="No person may be returned to a territory where they face persecution or serious "
                          "harm. This is binding on Bangladesh as customary international law even though "
                          "Bangladesh has not ratified the 1951 Refugee Convention.",
        ),
        LegalRight(
            right="UNHCR mandate protection for stateless persons",
            statute="UNHCR Statute 1950, Paragraph 6(A)(ii)",
            jurisdiction="UNIVERSAL", source_url="",
            plain_english="UNHCR has a mandate to protect stateless persons. File an emergency escalation "
                          "directly with UNHCR Cox's Bazar — they have operational authority in this region.",
        ),
        LegalRight(
            right="Right to seek asylum",
            statute="Universal Declaration of Human Rights, Article 14",
            jurisdiction="UNIVERSAL", source_url="",
            plain_english="Everyone has the right to seek and enjoy asylum from persecution in other countries.",
        ),
    ],
    CaseType.IMMIGRATION: [
        LegalRight(
            right="Non-refoulement",
            statute="Customary International Law / UNHCR Statute Article 33",
            jurisdiction="UNIVERSAL", source_url="",
            plain_english="Binding on all states regardless of 1951 Convention ratification. "
                          "Return to Myanmar where persecution is documented is prohibited.",
        ),
        LegalRight(
            right="Right to seek asylum",
            statute="Universal Declaration of Human Rights, Article 14",
            jurisdiction="UNIVERSAL", source_url="",
            plain_english="Everyone has the right to seek and enjoy asylum from persecution.",
        ),
    ],
    CaseType.HUMAN_RIGHTS: [
        LegalRight(
            right="Prohibition of torture and cruel treatment",
            statute="UN Convention Against Torture, Article 1",
            jurisdiction="UNIVERSAL", source_url="",
            plain_english="No one may be subjected to torture or cruel, inhuman, or degrading treatment. "
                          "Bangladesh ratified CAT in 1998.",
        ),
        LegalRight(
            right="Right to life and security of person",
            statute="Universal Declaration of Human Rights, Article 3",
            jurisdiction="UNIVERSAL", source_url="",
            plain_english="Everyone has the right to life, liberty, and security of person.",
        ),
    ],
}

# Rights that apply regardless of jurisdiction and stateless status
UNIVERSAL_RIGHTS = {
    CaseType.LABOR: [
        LegalRight(right="Right to just and favourable conditions of work",
                   statute="Universal Declaration of Human Rights, Article 23",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to just conditions of work, equal pay, and "
                                 "protection against unemployment."),
        LegalRight(right="Right to fair pay and reasonable working hours",
                   statute="Universal Declaration of Human Rights, Article 24",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to fair remuneration and reasonable working hours. "
                                 "Unpaid overtime violates this right."),
        LegalRight(right="Protection of wages against unlawful withholding",
                   statute="ILO Convention No. 95 — Protection of Wages (1949)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Wages must be paid in full, regularly, and directly to the worker."),
        LegalRight(right="Protection against retaliatory dismissal",
                   statute="ILO Convention No. 158 — Termination of Employment (1982)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Termination for raising a wage complaint is unlawful retaliation under "
                                 "international labour standards."),
    ],
    CaseType.HOUSING: [
        LegalRight(right="Right to adequate housing",
                   statute="ICESCR Article 11",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to adequate housing. Forced eviction without "
                                 "legal notice violates international law."),
        LegalRight(right="Protection from arbitrary deprivation of property",
                   statute="Universal Declaration of Human Rights, Article 17",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="No one may be deprived of their home without lawful due process "
                                 "and a court order."),
    ],
    CaseType.CRIMINAL: [
        LegalRight(right="Prohibition of arbitrary detention",
                   statute="Universal Declaration of Human Rights, Article 9",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="No one may be arrested or detained arbitrarily without legal basis."),
        LegalRight(right="Right to be informed of charges",
                   statute="ICCPR Article 9(2)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Anyone arrested must be informed promptly of charges in a language "
                                 "they understand."),
        LegalRight(right="Right to legal representation",
                   statute="ICCPR Article 14(3)(d)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Every accused person has the right to legal representation. If they "
                                 "cannot afford a lawyer, one must be provided."),
    ],
    CaseType.FAMILY: [
        LegalRight(right="Protection of the family unit",
                   statute="Universal Declaration of Human Rights, Article 16(3)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="The family is a fundamental unit of society entitled to protection "
                                 "by the State."),
        LegalRight(right="Best interests of the child",
                   statute="UN Convention on the Rights of the Child, Article 3",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="In all decisions concerning children, the best interests of the child "
                                 "must be the primary consideration."),
    ],
    CaseType.IMMIGRATION: [
        LegalRight(right="Right to seek asylum",
                   statute="Universal Declaration of Human Rights, Article 14",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to seek and enjoy asylum from persecution."),
        LegalRight(right="Non-refoulement protection",
                   statute="1951 Refugee Convention, Article 33",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="No person may be returned to a country where they face persecution "
                                 "or serious harm."),
    ],
    CaseType.CONSUMER: [
        LegalRight(right="Right to effective legal remedy",
                   statute="Universal Declaration of Human Rights, Article 8",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to an effective remedy by a competent tribunal."),
        LegalRight(right="UN Consumer Protection Guidelines",
                   statute="UN Guidelines for Consumer Protection (2015)",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Consumers have rights to safety, information, choice, and redress "
                                 "under UN guidelines."),
    ],
    CaseType.CIVIL: [
        LegalRight(right="Right to effective legal remedy",
                   statute="Universal Declaration of Human Rights, Article 8",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to an effective remedy by a competent "
                                 "national tribunal."),
        LegalRight(right="Right to fair trial",
                   statute="Universal Declaration of Human Rights, Article 10",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone is entitled to a fair and public hearing by an independent "
                                 "tribunal."),
    ],
    CaseType.HUMAN_RIGHTS: [
        LegalRight(right="Prohibition of torture",
                   statute="UN Convention Against Torture, Article 1",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="No one may be tortured or subjected to cruel or degrading treatment "
                                 "under any circumstances."),
        LegalRight(right="Right to equality before the law",
                   statute="Universal Declaration of Human Rights, Article 7",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="All people are equal before the law and entitled to equal protection "
                                 "without discrimination."),
    ],
    CaseType.UNKNOWN: [
        LegalRight(right="Right to equality before the law",
                   statute="Universal Declaration of Human Rights, Article 7",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="All people are equal before the law and entitled to equal protection."),
        LegalRight(right="Right to effective legal remedy",
                   statute="Universal Declaration of Human Rights, Article 8",
                   jurisdiction="UNIVERSAL", source_url="",
                   plain_english="Everyone has the right to an effective remedy by a competent national "
                                 "tribunal."),
    ],
}

# When a criminal case also involves deportation/immigration, pull these extra types
CASE_TYPE_ESCALATION_MAP = {
    CaseType.CRIMINAL: [CaseType.IMMIGRATION, CaseType.HUMAN_RIGHTS],
    CaseType.IMMIGRATION: [CaseType.HUMAN_RIGHTS],
    CaseType.HOUSING: [CaseType.HUMAN_RIGHTS],
    CaseType.FAMILY: [CaseType.HUMAN_RIGHTS],
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
              f"({len(set(k[0] for k in db))} countries × "
              f"{len(set(k[1] for k in db))} case types)")

    except FileNotFoundError:
        print("[Retriever] WARNING: jurisdictions.yaml not found")
    except Exception as e:
        print(f"[Retriever] ERROR loading yaml: {e}")
    return db


# Load once at startup — shared across all requests
_STATUTE_DB = _load_yaml_statutes()

ENUM_TO_STR = {
    CaseType.HOUSING:      "housing",
    CaseType.LABOR:        "labor",
    CaseType.CRIMINAL:     "criminal",
    CaseType.FAMILY:       "family",
    CaseType.IMMIGRATION:  "immigration",
    CaseType.CONSUMER:     "consumer",
    CaseType.CIVIL:        "civil",
    CaseType.HUMAN_RIGHTS: "human_rights",
    CaseType.UNKNOWN:      "general",
}


class LegalKnowledgeRetriever:
    """
    Retrieves statutes for a given case from the 100-case YAML database.

    Key behaviours added over v1:
    - Multi-label retrieval: pulls statutes for all relevant case types, not just
      the primary classification. A criminal case involving deportation also pulls
      immigration and human_rights statutes automatically.
    - Stateless person mode: when case.is_stateless is True, domestic statutes are
      bypassed entirely and STATELESS_RIGHTS are used instead. This prevents the
      system from citing domestic criminal procedure to a person who has no legal
      identity in that jurisdiction.
    - Coverage confidence scoring: computes a score based on how many local statutes
      were found vs. the expected minimum. If coverage is below threshold, the case
      is flagged LOW_RETRIEVAL_CONFIDENCE and human lawyer escalation becomes
      mandatory — the system no longer silently fills gaps with generic templates.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15)

    async def _query_courtlistener(
        self, query: str, jurisdiction: str
    ) -> list[LegalRight]:
        results = []
        try:
            resp = await self.client.get(
                f"{COURTLISTENER_BASE}/search/",
                params={
                    "q": query,
                    "type": "o",
                    "order_by": "score desc",
                    "stat_Precedential": "on",
                },
            )
            for hit in resp.json().get("results", [])[:2]:
                results.append(LegalRight(
                    right=hit.get("caseName", ""),
                    statute=hit.get("citation", ""),
                    jurisdiction=jurisdiction,
                    source_url=f"https://www.courtlistener.com"
                               f"{hit.get('absolute_url', '')}",
                    plain_english=hit.get("snippet", "")[:200],
                ))
        except Exception as e:
            print(f"[Retriever] CourtListener failed: {e}")
        return results

    def _get_local_rights(
        self, country: str, case_type: CaseType
    ) -> list[LegalRight]:
        ct_str = ENUM_TO_STR.get(case_type, "general")

        # Exact match
        rights = _STATUTE_DB.get((country, ct_str), [])
        if rights:
            return rights

        # Aliased case types
        if case_type == CaseType.CIVIL:
            rights = _STATUTE_DB.get((country, "debt"), [])
        elif case_type == CaseType.LABOR:
            base = _STATUTE_DB.get((country, "labor"), [])
            disc = _STATUTE_DB.get((country, "employment_discrimination"), [])
            return base + disc

        # Parent jurisdiction fallback (e.g. "US-CA" → "US")
        if not rights and "-" in country:
            parent = country.split("-")[0]
            rights = _STATUTE_DB.get((parent, ct_str), [])

        return rights

    def _compute_coverage(
        self, country: str, case_type: CaseType, local_count: int
    ) -> float:
        """
        Returns a coverage score between 0.0 and 1.0.
        0.0 = no local statutes found at all.
        1.0 = found at least EXPECTED_LOCAL_STATUTES.
        Used to decide whether to flag LOW_RETRIEVAL_CONFIDENCE.
        """
        return min(1.0, local_count / EXPECTED_LOCAL_STATUTES)

    def _resolve_case_types(self, case) -> list[CaseType]:
        """
        Returns the full list of case types to retrieve statutes for.
        Starts with the primary classification, then adds any escalation types
        triggered by the case flags (e.g. deportation risk, minor in detention).
        """
        types = [case.case_type]

        # Always escalate based on primary type
        types += CASE_TYPE_ESCALATION_MAP.get(case.case_type, [])

        # Minor in detention → always add CRC-based rights
        if getattr(case, "involves_minor", False):
            if CaseType.HUMAN_RIGHTS not in types:
                types.append(CaseType.HUMAN_RIGHTS)

        # Deportation risk → always pull immigration
        if getattr(case, "deportation_risk", False):
            if CaseType.IMMIGRATION not in types:
                types.append(CaseType.IMMIGRATION)

        return list(dict.fromkeys(types))  # deduplicate, preserve order

    async def retrieve(self, case) -> list[LegalRight]:
        rights = []
        total_local = 0

        is_stateless = getattr(case, "is_stateless", False)
        case_types = self._resolve_case_types(case)

        if is_stateless:
            # Domestic statutes are meaningless for a stateless person.
            # Pull international-only rights for all relevant case types.
            for ct in case_types:
                stateless = STATELESS_RIGHTS.get(ct, [])
                rights.extend(stateless)
                print(f"[Retriever] Stateless mode — {len(stateless)} intl rights "
                      f"for {ENUM_TO_STR.get(ct, '?')}")

            # Coverage is always flagged as low for stateless cases regardless
            # of how many rights we found — human lawyer is mandatory.
            case.flags = getattr(case, "flags", [])
            if "LOW_RETRIEVAL_CONFIDENCE" not in case.flags:
                case.flags.append("LOW_RETRIEVAL_CONFIDENCE")
            case.mandate_human_lawyer = True
            print(f"[Retriever] Stateless person detected — "
                  f"human lawyer escalation mandatory")

        else:
            # Standard path: local statutes for all resolved case types
            for ct in case_types:
                local = self._get_local_rights(case.country, ct)
                rights.extend(local)
                total_local += len(local)
                print(f"[Retriever] {len(local)} local statutes → "
                      f"{case.country}/{ENUM_TO_STR.get(ct, '?')}")

            # Coverage confidence check on primary case type only
            primary_local = self._get_local_rights(case.country, case.case_type)
            coverage = self._compute_coverage(
                case.country, case.case_type, len(primary_local)
            )

            case.flags = getattr(case, "flags", [])
            if coverage < 0.5:
                case.flags.append("LOW_RETRIEVAL_CONFIDENCE")
                case.mandate_human_lawyer = True
                print(f"[Retriever] WARNING: Low coverage ({coverage:.0%}) for "
                      f"{case.country}/{ENUM_TO_STR.get(case.case_type, '?')} — "
                      f"human lawyer escalation mandatory")
            else:
                print(f"[Retriever] Coverage: {coverage:.0%} for "
                      f"{case.country}/{ENUM_TO_STR.get(case.case_type, '?')}")

            # Fill remaining slots with international rights for primary type
            intl = UNIVERSAL_RIGHTS.get(
                case.case_type, UNIVERSAL_RIGHTS[CaseType.UNKNOWN]
            )
            needed = max(0, 4 - len(rights))
            rights.extend(intl[:needed])

            # Live CourtListener for US cases
            if case.country == "US" and len(rights) < 5:
                query = (
                    f"{ENUM_TO_STR.get(case.case_type, '')} "
                    f"{' '.join(case.key_facts[:2])}"
                )
                rights.extend(
                    await self._query_courtlistener(query, case.jurisdiction)
                )

        print(f"[Retriever] Total: {len(rights)} rights returned | "
              f"flags: {getattr(case, 'flags', [])}")
        return rights

    async def close(self):
        await self.client.aclose()