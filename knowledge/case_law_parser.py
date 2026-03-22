# knowledge/case_law_parser.py
# Parses responses from CourtListener and GovInfo APIs
# Extracts relevant holdings, statutes, and plain-language summaries
# Used by the retriever to convert raw API data into LegalRight objects

import re
from intake.base import LegalRight


class CourtListenerParser:
    """
    Parses CourtListener API responses into structured LegalRight objects.
    CourtListener is the largest free legal database — 4M+ opinions.
    """

    def parse_opinion(self, hit: dict, jurisdiction: str) -> LegalRight | None:
        """Parse a single CourtListener search hit."""
        case_name = hit.get("caseName", "").strip()
        citation  = hit.get("citation", "")
        snippet   = hit.get("snippet", "").strip()
        url       = f"https://www.courtlistener.com{hit.get('absolute_url', '')}"

        if not case_name or not snippet:
            return None

        # Clean HTML tags from snippet
        clean_snippet = re.sub(r"<[^>]+>", "", snippet)
        clean_snippet = re.sub(r"\s+", " ", clean_snippet).strip()

        # Extract the legal holding from the snippet
        plain_english = self._extract_holding(clean_snippet)

        return LegalRight(
            right=case_name,
            statute=citation if citation else case_name,
            jurisdiction=jurisdiction,
            source_url=url,
            plain_english=plain_english[:300] if plain_english else clean_snippet[:200],
        )

    def _extract_holding(self, text: str) -> str:
        """Extract the key legal holding from opinion text."""
        # Look for common holding patterns
        patterns = [
            r"[Ww]e hold that (.+?)\.",
            r"[Ww]e conclude that (.+?)\.",
            r"[Hh]eld that (.+?)\.",
            r"[Tt]he court found that (.+?)\.",
            r"[Tt]he court held (.+?)\.",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        # Fallback: return first 200 chars
        return text[:200]

    def parse_search_results(self, data: dict, jurisdiction: str) -> list[LegalRight]:
        """Parse a full CourtListener search response."""
        rights = []
        for hit in data.get("results", [])[:5]:
            right = self.parse_opinion(hit, jurisdiction)
            if right:
                rights.append(right)
        return rights


class GovInfoParser:
    """
    Parses GovInfo API responses (US federal law, regulations, congressional records).
    Free, no API key required for basic access.
    """

    def parse_result(self, item: dict, jurisdiction: str = "US") -> LegalRight | None:
        """Parse a single GovInfo result."""
        title     = item.get("title", "").strip()
        doc_class = item.get("docClass", "")
        package   = item.get("packageId", "")
        date      = item.get("dateIssued", "")

        if not title:
            return None

        url = f"https://www.govinfo.gov/content/pkg/{package}/html/{package}.htm" if package else ""

        return LegalRight(
            right=title,
            statute=f"{doc_class}: {title}" if doc_class else title,
            jurisdiction=jurisdiction,
            source_url=url,
            plain_english=f"Federal law: {title}. Published {date}." if date else f"Federal law: {title}.",
        )

    def parse_search_results(self, data: dict) -> list[LegalRight]:
        """Parse full GovInfo search response."""
        rights = []
        packages = data.get("packages", [])
        for item in packages[:3]:
            right = self.parse_result(item)
            if right:
                rights.append(right)
        return rights


class StatuteTextExtractor:
    """
    Extracts key provisions from statute text.
    Used to summarize long statutory sections into plain English.
    """

    def extract_key_provisions(self, text: str, max_length: int = 300) -> str:
        """Extract the most relevant provisions from statute text."""
        if not text:
            return ""

        # Clean formatting
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\([a-z]\)", "", text)   # remove subsection markers

        # Find first substantive sentence (skip definitions and preambles)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sent in sentences:
            if len(sent) > 50 and not sent.lower().startswith(("for purposes", "as used", "the term")):
                return sent[:max_length].strip()

        return text[:max_length].strip()

    def plain_english_summary(self, statute_text: str, right_type: str) -> str:
        """Generate a plain English summary of a statute."""
        if not statute_text:
            return f"You have legal rights regarding {right_type}."

        key = self.extract_key_provisions(statute_text)
        if not key:
            return f"This law protects your rights in {right_type} situations."

        return key
