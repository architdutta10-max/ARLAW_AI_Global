from app import llm


def test_provider_order_filters_unknown(monkeypatch):
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "ollama,unknown,groq")
    assert llm.provider_order() == ["ollama", "groq"]


def test_generate_falls_back_after_provider_error(monkeypatch):
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "groq,ollama")
    monkeypatch.setattr(llm, "PROVIDERS", {
        "groq": lambda payload: (_ for _ in ()).throw(RuntimeError("offline")),
        "ollama": lambda payload: ("answer", "qwen3:1.7b"),
    })
    answer, error, meta = llm.generate([{"role": "user", "content": "Explain contract law"}])
    assert answer == "answer"
    assert error is None
    assert meta["provider"] == "ollama"
    assert meta["fallback_used"] is True


def test_generate_reports_all_provider_failures(monkeypatch):
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "groq")
    monkeypatch.setattr(llm, "PROVIDERS", {"groq": lambda payload: (_ for _ in ()).throw(RuntimeError("offline"))})
    answer, error, meta = llm.generate([{"role": "user", "content": "test"}])
    assert answer is None
    assert "All configured AI providers failed" in error
    assert meta["provider"] is None


def test_task_classification():
    assert llm.classify_task("Explain GST tax for FY 2025") == "finance_tax"
    assert llm.classify_task("Translate this paragraph into Hindi") == "translation"
    assert llm.classify_task("How do I file a civil suit?") == "civil_procedure"
    assert llm.classify_task("Explain constitutional law") == "legal_research"


def test_task_specific_provider_route(monkeypatch):
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "groq,ollama")
    monkeypatch.setenv("ARLAW_ROUTE_FINANCE_TAX", "ollama,groq")
    assert llm.provider_order("finance_tax") == ["ollama", "groq"]
    assert llm.provider_order("general") == ["groq", "ollama"]


def test_citation_validation_flags_unknown_labels():
    result = llm.validate_citations("See [S1] and [S4].", ["S1", "S2"])
    assert result["valid"] == ["S1"]
    assert result["invalid"] == ["S4"]
    assert result["status"] == "invalid_reference"


def test_generate_includes_task_and_citation_metadata(monkeypatch):
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "ollama")
    monkeypatch.setenv("ARLAW_MULTI_MODEL_REVIEW", "false")
    monkeypatch.setattr(llm, "PROVIDERS", {"ollama": lambda payload: ("Use [S1] as authority.", "test-model")})
    answer, error, meta = llm.generate([{"role": "user", "content": "Explain contract law"}], "[S1] Act excerpt", ["S1"])
    assert error is None
    assert "[S1]" in answer
    assert meta["task"] == "legal_research"
    assert meta["citation_validation"]["valid"] == ["S1"]


def test_peer_review_uses_other_configured_provider(monkeypatch):
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "groq,ollama")
    monkeypatch.setenv("ARLAW_MULTI_MODEL_REVIEW", "true")
    monkeypatch.setattr(llm, "PROVIDERS", {
        "groq": lambda payload: ("Primary answer.", "primary-model"),
        "ollama": lambda payload: ("Review: verify the effective date.", "review-model"),
    })
    answer, error, meta = llm.generate([{"role": "user", "content": "Explain legal precedent"}])
    assert error is None
    assert "Independent model review" in answer
    assert meta["reviewers"][0]["provider"] == "ollama"


def test_invalid_task_route_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "groq,ollama")
    monkeypatch.setenv("ARLAW_ROUTE_LEGAL_RESEARCH", "not-a-provider")
    assert llm.provider_order("legal_research") == ["groq", "ollama"]


def test_professional_task_classification():
    assert llm.classify_task("Help me prepare a legal memo for my client") == "lawyer_assistance"
    assert llm.classify_task("Prepare a bank reconciliation and trial balance") == "accounting"
    assert llm.classify_task("Calculate my GST return and income tax filing") == "ca_tax"
    assert llm.classify_task("Create a neutral evidence matrix for judicial research") == "judicial_research"
