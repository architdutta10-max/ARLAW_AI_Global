"""Conservative clarification checks for underspecified legal references.

These checks do not decide what a phrase means. They prevent the model from
silently guessing an issuing body, instrument, session, or jurisdiction.
"""
from __future__ import annotations

import re


def clarification_for(question: str, jurisdiction: str = "GLOBAL") -> dict | None:
    q = " ".join((question or "").split())
    if not q:
        return None

    # Agenda numbers are not globally unique: they need an issuing body and date/session.
    agenda = re.search(r"\bagenda\s*(?:no\.?|number)?\s*#?\s*(\d+[A-Za-z]?)\b", q, re.I)
    if agenda:
        has_issuer = bool(re.search(
            r"\b(parliament|lok sabha|rajya sabha|un|united nations|security council|"
            r"assembly|committee|council|board|cabinet|municipal|company|organisation|organization)\b",
            q, re.I
        ))
        has_session = bool(re.search(r"\b(session|meeting|dated|on\s+\d|\b20\d{2}\b)\b", q, re.I))
        if not (has_issuer and has_session):
            return {
                "code": "ambiguous_agenda_reference",
                "term": agenda.group(0),
                "question": (
                    f"Which organisation or legislative body issued Agenda {agenda.group(1)}, "
                    "and for which meeting, session, or date?"
                ),
                "reason": "Agenda numbers are reused by different organisations and sessions.",
            }

    # A numbered resolution requires the issuing institution and, often, year/date.
    resolution = re.search(r"\bresolution\s*(?:no\.?|number)?\s*#?\s*(\d{1,5})\b", q, re.I)
    if resolution:
        has_issuer = bool(re.search(
            r"\b(un|united nations|security council|general assembly|parliament|"
            r"council of europe|eu|european union|court|municipal|legislature)\b", q, re.I
        ))
        has_date = bool(re.search(r"\b(19|20)\d{2}\b", q))
        if not (has_issuer and has_date):
            return {
                "code": "ambiguous_resolution_reference",
                "term": resolution.group(0),
                "question": (
                    f"Which body issued Resolution {resolution.group(1)}, and what year or date "
                    "should I use?"
                ),
                "reason": "Resolution numbers are not unique across institutions or years.",
            }

    # Article/section numbers without an instrument are unsafe to interpret as law.
    provision = re.search(r"\b(art(?:icle)?|sec(?:tion)?)\s*\.?\s*(\d+[A-Za-z]?)\b", q, re.I)
    if provision:
        has_instrument = bool(re.search(
            r"\b(constitution|act|acts|code|statute|regulation|regulations|directive|treaty|convention|"
            r"charter|protocol|ordinance|rules|bylaws?|criminal procedure|penal code|civil procedure|"
            r"ipc|crpc|cpc|bns|bnss|bsa|gdpr|echr|iccpr|icescr|ucc|u\.?s\.?c|c\.?f\.?r|"
            r"agreement|contract|lease|deed|association|memorandum)\b", q, re.I
        ))
        if not has_instrument:
            return {
                "code": "ambiguous_legal_provision",
                "term": provision.group(0),
                "question": (
                    f"Which law or legal instrument contains {provision.group(0)}? "
                    "Please provide its name and, if relevant, the country or jurisdiction."
                ),
                "reason": "Provision numbers repeat across different laws and jurisdictions.",
            }

    return None
