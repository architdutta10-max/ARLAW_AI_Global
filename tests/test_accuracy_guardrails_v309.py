from app import llm


def test_source_prompt_requires_evidence_audit_and_disclaims_verification():
    payload = llm._messages(
        [{"role": "user", "content": "Explain a legal rule"}],
        context="[S1] Example statute excerpt",
        task="legal_research",
    )
    packet = "\n".join(item["content"] for item in payload)
    assert "audit each material factual/legal proposition" in packet
    assert "This is not independent verification" in packet


def test_generate_exposes_limits_of_accuracy_safeguards(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "groq")
    monkeypatch.setattr(
        llm,
        "PROVIDERS",
        {"groq": lambda payload: ("A source-backed answer [S1].", "test-model")},
    )
    answer, error, meta = llm.generate(
        [{"role": "user", "content": "Explain Article 21 of the Constitution of India"}],
        "[S1] Article 21 excerpt",
        ["S1"],
    )
    assert error is None
    assert answer.endswith("[S1].")
    assert meta["accuracy_review"]["claim_support_verified"] is False
    assert meta["accuracy_review"]["source_currency_verified"] is False
