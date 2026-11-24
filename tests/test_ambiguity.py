from app.ambiguity import clarification_for


def test_agenda_number_without_issuer_and_session_requests_clarification():
    result = clarification_for("What is Agenda 51?", "IN")
    assert result["code"] == "ambiguous_agenda_reference"
    assert "organisation" in result["question"]


def test_agenda_with_issuer_and_session_is_not_blocked():
    assert clarification_for("What is the Lok Sabha agenda for the 2026 winter session?", "IN") is None


def test_resolution_without_issuer_and_year_requests_clarification():
    result = clarification_for("Explain Resolution 242")
    assert result["code"] == "ambiguous_resolution_reference"


def test_article_number_without_instrument_requests_clarification():
    result = clarification_for("Explain Article 21")
    assert result["code"] == "ambiguous_legal_provision"


def test_article_with_instrument_is_not_blocked():
    assert clarification_for("Explain Article 21 of the Constitution of India", "IN") is None


def test_general_question_is_not_blocked():
    assert clarification_for("How does contract law generally work?") is None


def test_chat_endpoint_returns_clarification_without_calling_model(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as main

    monkeypatch.setattr(main, "_rate_limit", lambda *args, **kwargs: None)
    def unexpected(*args, **kwargs):
        raise AssertionError("Model should not be called for an ambiguous reference")
    monkeypatch.setattr(main, "generate", unexpected)
    with TestClient(main.app) as client:
        response = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "What is Agenda 51?"}],
            "jurisdiction": "IN",
            "use_knowledge": True,
        })
    assert response.status_code == 200
    body = response.json()
    assert body["needs_clarification"] is True
    assert body["citations"] == []
    assert "Which organisation" in body["answer"]


def test_coverage_endpoint_is_explicit_about_registry_limits():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        response = client.get("/api/coverage")
    assert response.status_code == 200
    body = response.json()
    assert "does not prove" in body["coverage_scope"]
    assert any(item["code"] == "IN" for item in body["jurisdictions"])
