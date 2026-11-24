from app import llm


def test_provider_order_filters_unknown_and_respects_enabled_providers(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("OLLAMA_ENABLED", "false")
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "ollama,unknown,groq")
    assert llm.provider_order() == ["groq"]


def test_ollama_can_be_primary_without_groq_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_ENABLED", "true")
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "ollama,groq")
    assert llm.provider_order() == ["ollama"]


def test_groq_only_provider_failure_is_reported(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("OLLAMA_ENABLED", "false")
    monkeypatch.setattr(llm, "PROVIDERS", {
        "groq": lambda payload: (_ for _ in ()).throw(RuntimeError("offline")),
    })
    answer, error, meta = llm.generate([{"role": "user", "content": "Explain contract law"}])
    assert answer is None
    assert "All configured AI providers failed" in error
    assert meta["provider"] is None


def test_generate_reports_all_provider_failures(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
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
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "groq,ollama")
    monkeypatch.setenv("OLLAMA_ENABLED", "true")
    monkeypatch.setenv("ARLAW_ROUTE_FINANCE_TAX", "ollama,groq")
    assert llm.provider_order("finance_tax") == ["ollama", "groq"]
    assert llm.provider_order("general") == ["groq", "ollama"]


def test_citation_validation_flags_unknown_labels():
    result = llm.validate_citations("See [S1] and [S4].", ["S1", "S2"])
    assert result["valid"] == ["S1"]
    assert result["invalid"] == ["S4"]
    assert result["status"] == "invalid_reference"


def test_generate_includes_task_and_citation_metadata(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "groq")
    monkeypatch.setenv("ARLAW_MULTI_MODEL_REVIEW", "false")
    monkeypatch.setattr(llm, "PROVIDERS", {"groq": lambda payload: ("Use [S1] as authority.", "test-model")})
    answer, error, meta = llm.generate([{"role": "user", "content": "Explain contract law"}], "[S1] Act excerpt", ["S1"])
    assert error is None
    assert "[S1]" in answer
    assert meta["task"] == "legal_research"
    assert meta["citation_validation"]["valid"] == ["S1"]


def test_peer_review_uses_other_configured_provider(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("ARLAW_MULTI_MODEL_REVIEW", "true")
    monkeypatch.setattr(llm, "PROVIDERS", {"groq": lambda payload: ("Primary answer.", "primary-model")})
    answer, error, meta = llm.generate([{"role": "user", "content": "Explain legal precedent"}])
    assert error is None
    assert "Independent model review" not in answer
    assert meta["review_enabled"] is False


def test_invalid_task_route_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "groq,ollama")
    monkeypatch.setenv("OLLAMA_ENABLED", "false")
    monkeypatch.setenv("ARLAW_ROUTE_LEGAL_RESEARCH", "not-a-provider")
    assert llm.provider_order("legal_research") == []


def test_professional_task_classification():
    assert llm.classify_task("Help me prepare a legal memo for my client") == "lawyer_assistance"
    assert llm.classify_task("Prepare a bank reconciliation and trial balance") == "accounting"
    assert llm.classify_task("Calculate my GST return and income tax filing") == "ca_tax"
    assert llm.classify_task("Create a neutral evidence matrix for judicial research") == "judicial_research"


def test_chat_message_schema_limits_content():
    from app.main import ChatMessage
    import pytest
    assert ChatMessage(role="user", content="hello").content == "hello"
    with pytest.raises(Exception):
        ChatMessage(role="user", content="")



def test_repetition_report_detects_repeated_sections():
    repeated = "Section 54 has a unique rule in the source document.\n\n" * 4
    result = llm.repetition_report(repeated)
    assert result["is_repetitive"] is True
    assert result["repeated_blocks"] == 1


def test_generate_attempts_repair_for_repeated_sections(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("OLLAMA_ENABLED", "false")
    calls = []
    repeated = "Section 54 has a repeated generic description that is long enough to flag.\n\n" * 4
    corrected = "Section 54: verified provision A.\n\nSection 55: verified provision B.\n\nSection 56: verified provision C."
    def fake_provider(payload):
        calls.append(payload)
        return (repeated, "test-model") if len(calls) == 1 else (corrected, "test-model")
    monkeypatch.setattr(llm, "PROVIDERS", {"groq": fake_provider})
    answer, error, meta = llm.generate([{"role": "user", "content": "List sections 54 to 56"}])
    assert error is None
    assert answer == corrected
    assert meta["repetition_repaired"] is True
    assert len(calls) == 2


def test_generate_continues_only_on_length_finish_reason(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("OLLAMA_ENABLED", "false")
    calls = []
    def fake_provider(payload):
        calls.append(payload)
        if len(calls) == 1:
            return ("Beginning of answer.", "test-model", "length")
        return ("Completed ending.", "test-model", "stop")
    monkeypatch.setattr(llm, "PROVIDERS", {"groq": fake_provider})
    answer, error, meta = llm.generate([{"role": "user", "content": "Explain a legal topic"}])
    assert error is None
    assert "Beginning of answer." in answer and "Completed ending." in answer
    assert meta["continuations"] == 1
    assert meta["incomplete"] is False


def test_repetition_warning_survives_failed_repair(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("OLLAMA_ENABLED", "false")
    repeated = "A repeated legal section description that should trigger the warning.\n\n" * 4
    monkeypatch.setattr(llm, "PROVIDERS", {"groq": lambda payload: (repeated, "test-model")})
    answer, error, meta = llm.generate([{"role": "user", "content": "List legal sections"}])
    assert error is None
    assert meta["quality"]["is_repetitive"] is True
    assert "quality_warning" in meta


def test_messages_budget_long_history():
    messages = [{"role": "user", "content": "x" * 5000} for _ in range(30)]
    payload = llm._messages(messages, context="c" * 20000, task="general")
    assert len(payload) <= 14
    assert sum(len(str(x.get("content", ""))) for x in payload) < 18000
    assert payload[-1]["role"] == "user"


def test_retry_delay_parses_groq_body():
    class Response:
        headers = {}
        text = '{"error":{"message":"Please try again in 27.9075s."}}'
    assert 27 < llm._retry_delay(Response()) < 30


def test_retry_delay_parses_retry_after_header():
    class Response:
        headers = {"retry-after": "3"}
        text = ""
    assert 3 <= llm._retry_delay(Response()) <= 4


def test_citation_validation_accepts_bold_labels_and_does_not_claim_verification():
    result = llm.validate_citations("See **S1** and [S2]; **S9** is unknown.", ["S1", "S2"])
    assert result["cited"] == ["S1", "S2", "S9"]
    assert result["valid"] == ["S1", "S2"]
    assert result["invalid"] == ["S9"]
    assert result["status"] == "invalid_reference"
    assert "not verified" in result["scope"]


def test_provider_failure_details_are_safe_and_specific():
    import requests

    assert llm._provider_failure_detail(
        "groq", RuntimeError("GROQ_API_KEY is not configured")
    ) == "groq: API key not configured"

    assert llm._provider_failure_detail(
        "ollama", RuntimeError("Ollama returned an empty response")
    ) == "ollama: empty response"

    assert llm._provider_failure_detail(
        "groq", requests.Timeout()
    ) == "groq: timeout"

    assert llm._provider_failure_detail(
        "ollama", requests.ConnectionError()
    ) == "ollama: connection error"


def test_provider_failure_details_do_not_expose_unknown_error_text():
    secret_like_text = "private-token-example"
    result = llm._provider_failure_detail(
        "groq", RuntimeError(secret_like_text)
    )
    assert result == "groq: RuntimeError"
    assert secret_like_text not in result


def test_citation_coverage_detects_uncited_prose_paragraphs():
    answer = (
        "## Overview\n\n"
        "The rule applies to all persons within the territory. [S1]\n\n"
        "A second legal proposition is presented here without a citation."
    )
    result = llm.validate_citations(answer, ["S1"])
    assert result["paragraphs_checked"] == 2
    assert result["paragraphs_with_citations"] == 1
    assert result["uncited_paragraphs"] == 1
    assert result["coverage_status"] == "uncited_paragraphs_detected"
    assert "does not verify" in result["scope"]


def test_citation_coverage_does_not_claim_source_support():
    answer = (
        "This paragraph includes a citation label. [S1]\n\n"
        "Another paragraph also includes a citation label. **S1**"
    )
    result = llm.validate_citations(answer, ["S1"])
    assert result["paragraphs_checked"] == 2
    assert result["paragraphs_with_citations"] == 2
    assert result["uncited_paragraphs"] == 0
    assert result["coverage_status"] == "citation_labels_present_in_checked_paragraphs"
    assert result["status"] == "reference_exists_not_verified"


def test_citation_coverage_reports_missing_retrieved_sources():
    answer = "This paragraph contains a legal statement but no source label."
    result = llm.validate_citations(answer, [])
    assert result["coverage_status"] == "no_retrieved_sources"
    assert result["uncited_paragraphs"] == 1


def test_citation_coverage_ignores_headings_and_markdown_tables():
    answer = (
        "# Heading\n\n"
        "| Topic | Explanation |\n"
        "|---|---|\n"
        "| Rule | A table entry without a citation |\n\n"
        "This prose paragraph contains a citation. [S1]"
    )
    result = llm.validate_citations(answer, ["S1"])
    assert result["paragraphs_checked"] == 1
    assert result["paragraphs_with_citations"] == 1
    assert result["uncited_paragraphs"] == 0
