# intake/classifier.py
# Multilingual case intake — detects language, jurisdiction, case type, urgency
# Uses transformers for language detection and zero-shot classification
# No API key required for core classification

import re
import uuid
from datetime import datetime, timezone
from intake.base import LegalCase, CaseType, UrgencyLevel, CaseStatus


# ── Keyword maps for case type detection ──────────────────────────────────────

CASE_TYPE_KEYWORDS = {
    CaseType.HOUSING: [
        "evict", "eviction", "landlord", "tenant", "rent", "lease", "lockout",
        "illegal entry", "habitability", "deposit", "notice to quit", "mortgage",
        "foreclosure", "مالک مکان", "کرایہ", "بے دخلی", "sewa", "penggusuran",
    ],
    CaseType.CRIMINAL: [
        "arrest", "police", "charge", "criminal", "prison", "jail", "bail",
        "accused", "sentence", "detention", "گرفتار", "پولیس", "ditahan", "polisi",
    ],
    CaseType.LABOR: [
        "employer", "fired", "wrongful termination", "wage", "salary", "unpaid",
        "workplace", "discrimination", "harassment", "union", "ملازمت", "تنخواہ",
        "pemecatan", "upah", "majikan",
    ],
    CaseType.FAMILY: [
        "divorce", "custody", "child", "domestic violence", "abuse", "alimony",
        "marriage", "طلاق", "بچہ", "گھریلو تشدد", "perceraian", "hak asuh",
    ],
    CaseType.IMMIGRATION: [
        "visa", "deportation", "asylum", "refugee", "immigration", "undocumented",
        "citizenship", "border", "ویزا", "پناہ گزین", "deportasi", "suaka",
    ],
    CaseType.CONSUMER: [
        "fraud", "scam", "refund", "consumer", "product", "defective", "warranty",
        "debt collector", "dھوکہ", "واپسی", "penipuan", "konsumen",
    ],
    CaseType.CIVIL: [
        "lawsuit", "sue", "contract", "breach", "damages", "compensation",
        "negligence", "مقدمہ", "معاوضہ", "gugatan", "ganti rugi",
    ],
    CaseType.HUMAN_RIGHTS: [
        "torture", "discrimination", "rights violation", "freedom", "arbitrary",
        "persecution", "تعذیب", "امتیازی سلوک", "penyiksaan", "diskriminasi",
    ],
}

URGENCY_CRITICAL_KEYWORDS = [
    "tonight", "today", "right now", "immediately", "emergency", "arrested",
    "being evicted", "locked out", "deported", "آج رات", "ابھی", "فوری",
    "malam ini", "segera", "darurat",
]

URGENCY_HIGH_KEYWORDS = [
    "tomorrow", "this week", "court date", "hearing", "deadline", "24 hours",
    "کل", "عدالت", "besok", "sidang", "tenggat",
]

# ── Country/jurisdiction detection from keywords ──────────────────────────────

JURISDICTION_HINTS = {
    "PK": ["pakistan", "lahore", "karachi", "islamabad", "urdu", "pakistani",
           "پاکستان", "لاہور", "کراچی"],
    "IN": ["india", "delhi", "mumbai", "bangalore", "rupees", "indian court",
           "भारत", "दिल्ली"],
    "ID": ["indonesia", "jakarta", "surabaya", "pengadilan", "indonesian"],
    "US": ["united states", "america", "state of", "federal court", "section 1983"],
    "GB": ["england", "wales", "scotland", "uk", "british", "crown court"],
    "NG": ["nigeria", "lagos", "abuja", "nigerian court"],
    "BD": ["bangladesh", "dhaka", "bangladeshi"],
    "PH": ["philippines", "manila", "philippine court"],
    "ET": ["ethiopia", "addis ababa", "ethiopian"],
    "EG": ["egypt", "cairo", "egyptian court", "مصر"],
}


class CaseClassifier:
    """
    Multilingual case intake classifier.
    Detects: language, jurisdiction, case type, urgency.
    No API key required — uses pattern matching + optional transformers.
    """

    def __init__(self):
        self._lang_detector = None   # lazy loaded
        self._zero_shot = None       # lazy loaded

    def _get_lang_detector(self):
        if self._lang_detector is None:
            try:
                from langdetect import detect
                self._lang_detector = detect
            except ImportError:
                print("[Classifier] langdetect not installed — defaulting to 'en'")
                self._lang_detector = lambda x: "en"
        return self._lang_detector

    def detect_language(self, text: str) -> str:
        """Detect language of input text."""
        try:
            detector = self._get_lang_detector()
            return detector(text)
        except Exception:
            return "en"

    def detect_jurisdiction(self, text: str) -> tuple[str, str]:
        """Returns (country_code, jurisdiction_string)."""
        text_lower = text.lower()
        for country, hints in JURISDICTION_HINTS.items():
            if any(hint in text_lower for hint in hints):
                return country, country
        return "XX", "UNKNOWN"   # unknown jurisdiction

    def classify_case_type(self, text: str) -> CaseType:
        """Classify case type from keywords."""
        text_lower = text.lower()
        scores = {}
        for case_type, keywords in CASE_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[case_type] = score
        if not scores:
            return CaseType.UNKNOWN
        return max(scores, key=scores.get)

    def assess_urgency(self, text: str) -> UrgencyLevel:
        """Assess urgency from keywords and context."""
        text_lower = text.lower()
        if any(kw in text_lower for kw in URGENCY_CRITICAL_KEYWORDS):
            return UrgencyLevel.CRITICAL
        if any(kw in text_lower for kw in URGENCY_HIGH_KEYWORDS):
            return UrgencyLevel.HIGH
        # Criminal cases default to HIGH
        if any(kw in text_lower for kw in ["arrest", "jail", "prison", "گرفتار"]):
            return UrgencyLevel.HIGH
        return UrgencyLevel.MEDIUM

    def extract_key_facts(self, text: str) -> list[str]:
        """Extract key facts as bullet points."""
        facts = []
        sentences = re.split(r'[.!?]\s+', text)
        for sent in sentences[:10]:
            sent = sent.strip()
            if len(sent) > 20:
                facts.append(sent)
        return facts[:6]

    def intake(self, description: str) -> LegalCase:
        """
        Main entry point. Takes raw user description, returns LegalCase.
        This is called first in the pipeline.
        """
        case_id = str(uuid.uuid4())[:8].upper()
        language   = self.detect_language(description)
        country, jurisdiction = self.detect_jurisdiction(description)
        case_type  = self.classify_case_type(description)
        urgency    = self.assess_urgency(description)
        key_facts  = self.extract_key_facts(description)

        print(f"[Classifier] Case {case_id}: {case_type.value} | {urgency.name} | {country} | lang={language}")

        return LegalCase(
            case_id=case_id,
            raw_description=description,
            language=language,
            jurisdiction=jurisdiction,
            country=country,
            case_type=case_type,
            urgency=urgency,
            status=CaseStatus.INTAKE,
            key_facts=key_facts,
            metadata={"intake_timestamp": datetime.now(timezone.utc).isoformat()}
        )
