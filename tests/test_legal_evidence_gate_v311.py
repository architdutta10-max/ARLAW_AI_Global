from app.llm import _high_risk_legal_number_warning, _messages


def test_precise_legal_penalty_triggers_primary_source_warning():
    assert _high_risk_legal_number_warning(
        "The maximum fine is ₹250 crore.", "legal_research"
    )
    assert _high_risk_legal_number_warning(
        "Imprisonment may extend up to 3 years.", "legal_research"
    )


def test_commencement_date_triggers_primary_source_warning():
    assert _high_risk_legal_number_warning(
        "The provision came into force on 1 July 2024.", "legal_research"
    )


def test_ordinary_legal_explanation_does_not_trigger_number_warning():
    assert not _high_risk_legal_number_warning(
        "Article 21 protects life and personal liberty.", "legal_research"
    )


def test_retrieved_prompt_contains_numeric_evidence_gate():
    payload = _messages(
        [{"role": "user", "content": "Explain statutory penalties."}],
        context="[S1] Short excerpt.",
        task="legal_research",
    )
    prompt = "\n".join(item["content"] for item in payload)
    assert "strict evidence gate" in prompt.lower()
    assert "exact retrieved excerpt" in prompt.lower()
