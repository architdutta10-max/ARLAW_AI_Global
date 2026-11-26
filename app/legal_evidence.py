"""Narrow, deterministic evidence-span checks; not semantic legal verification."""
from __future__ import annotations
import re
from typing import Iterable

def _normalise(value: str) -> str:
    return " ".join(re.sub(r"\s+", " ", (value or "")).strip().split()).casefold()

def verify_exact_quote(quote: str, source_excerpts: Iterable[dict]) -> dict:
    """Check whether a supplied quote occurs verbatim after whitespace/case normalisation.

    A positive result proves only textual presence in the supplied excerpt, not that
    the quote supports a legal proposition, is authentic, current or authoritative.
    """
    needle = _normalise(quote)
    if not needle:
        return {"status":"invalid_empty_quote","exact_text_match":False,
                "semantic_support_verified":False}
    matches=[]
    for source in source_excerpts:
        content=_normalise(str(source.get("content","")))
        if needle in content:
            matches.append({
                "source_id":source.get("id"),
                "title":source.get("title"),
                "jurisdiction":source.get("jurisdiction"),
            })
    return {
        "status":"exact_text_match" if matches else "quote_not_found_in_supplied_excerpts",
        "exact_text_match":bool(matches),
        "matches":matches,
        "semantic_support_verified":False,
        "source_authenticity_verified":False,
        "source_currency_verified":False,
        "legal_correctness_verified":False,
        "scope":"Literal text-presence check only; no proposition-level semantic verification.",
    }
