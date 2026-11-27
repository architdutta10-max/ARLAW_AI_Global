"""Strict professional-purpose gate for ARLAW AI Global."""
from __future__ import annotations
import re

SCOPE_REFUSAL = (
    "I am ARLAW AI Global, a specialised legal, economic and judicial research assistant. "
    "Your question falls outside my designated scope. I can assist with legal research, "
    "legislation, case law, judicial analysis, economics, public policy and related "
    "professional workflows."
)

_PATTERNS = {
    "legal_research": r"\b(law|legal|legislation|statute|acts?\s+(?:of\s+)?(?:18|19|20)\d{2}|regulation|constitution|"
                      r"contract|tort|crime|criminal|civil|rights?|liability|compliance|"
                      r"jurisdiction|court|case law|judg(?:e)?ment|precedent|litigation|article\s+\d+|section\s+\d+|"
                      r"arbitration|legal notice|petition|plaint|bail|evidence|procedure)\b",
    "economics": r"\b(econom(?:y|ic|ics|ist)|inflation|gdp|fiscal|monetary|rbi|central bank|"
                 r"public finance|market structure|competition policy|trade policy|"
                 r"employment|labour market|unemployment|poverty|inequality|budget|"
                 r"interest rate|exchange rate|economic policy)\b",
    "governance": r"\b(governance|public policy|public administration|government|"
                  r"regulator|regulatory|institution|transparency|accountability|"
                  r"public procurement|welfare policy|administrative reform)\b",
    "professional": r"\b(accounting|bookkeeping|audit|tax|gst|income tax|tds|"
                    r"financial statement|balance sheet|due diligence|risk assessment|"
                    r"document review|contract review|legal drafting|case management|"
                    r"compliance workflow|forensic accounting)\b",
    "comparative": r"\b(comparative|cross.border|international law|international trade|"
                   r"treaty|convention|sanctions|foreign jurisdiction)\b",
}
_COMPILED = {k: re.compile(v, re.I) for k, v in _PATTERNS.items()}
_FOLLOW_UP = re.compile(
    r"^\s*(?:and|also|why|how|what about|explain|elaborate|continue|"
    r"give examples|more details|summarize|summarise|in simple words|"
    r"what does that mean|please explain)\b", re.I
)

def assess_scope(question: str, messages=None) -> dict:
    """Allow only designated professional subject matter; inherit clear follow-ups."""
    text = str(question or "").strip()
    matched = [name for name, pattern in _COMPILED.items() if pattern.search(text)]
    if matched:
        return {"in_scope": True, "categories": matched, "inherited": False}
    if messages and _FOLLOW_UP.search(text):
        for item in reversed(list(messages)[:-1]):
            if item.get("role") == "user":
                prior = str(item.get("content", ""))
                prior_matches = [name for name, pattern in _COMPILED.items() if pattern.search(prior)]
                if prior_matches:
                    return {"in_scope": True, "categories": prior_matches, "inherited": True}
                break
    return {"in_scope": False, "categories": [], "inherited": False}
