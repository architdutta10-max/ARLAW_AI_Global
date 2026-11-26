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


def test_full_bharatiya_nyaya_sanhita_name_prevents_false_ambiguity():
    question = (
        "Under the Bharatiya Nyaya Sanhita, 2023, explain Section 303(1) "
        "and Section 303(2) and identify the statutory source."
    )
    assert clarification_for(question, "IN") is None


def test_full_bharatiya_nagarik_suraksha_sanhita_name_prevents_false_ambiguity():
    assert clarification_for(
        "Explain Section 173 of the Bharatiya Nagarik Suraksha Sanhita, 2023", "IN"
    ) is None


def test_full_bharatiya_sakshya_adhiniyam_name_prevents_false_ambiguity():
    assert clarification_for(
        "Explain Section 63 of the Bharatiya Sakshya Adhiniyam, 2023", "IN"
    ) is None


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


def test_full_bns_question_reaches_retrieval_in_chat_endpoint(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as main

    monkeypatch.setattr(main, "_rate_limit", lambda *args, **kwargs: None)
    monkeypatch.setattr(main, "_retrieve_request", lambda *args, **kwargs: ([], [], "legal_research"))
    monkeypatch.setattr(main, "_must_abstain_without_legal_sources", lambda *args, **kwargs: True)

    question = (
        "Under the Bharatiya Nyaya Sanhita, 2023, explain Section 303(1) "
        "and Section 303(2) and identify the statutory source."
    )
    with TestClient(main.app) as client:
        response = client.post("/api/chat", json={
            "messages": [{"role": "user", "content": question}],
            "jurisdiction": "IN",
            "use_knowledge": True,
        })

    assert response.status_code == 200
    body = response.json()
    assert body["needs_clarification"] is False
    assert body["clarification"] is None
    assert "could not retrieve a jurisdiction-matched legal source" in body["answer"]


def test_bns_section_heading_and_full_punishment_are_retrievable_across_chunks(tmp_path, monkeypatch):
    from app import knowledge

    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "knowledge.db")
    knowledge.init_db()
    long_explanation = (
        "Explanation 1. A movable property is capable of being moved. "
        "Explanation 2. Consent may be express or implied. "
    ) * 18
    text = (
        "THE BHARATIYA NYAYA SANHITA, 2023. "
        + ("Preliminary statutory material unrelated to theft. " * 18)
        + "303. Theft.—(1) Whoever, intending to take dishonestly any movable property "
        "out of the possession of any person without that person's consent, moves that "
        "property in order to such taking, is said to commit theft. "
        + long_explanation
        + "(2) Whoever commits theft shall be punished with imprisonment of either "
        "description for a term which may extend to three years, or with fine, or with both. "
        "In case of second or subsequent conviction, rigorous imprisonment shall not be "
        "less than one year but may extend to five years and with fine. "
        "Provided that where the value is less than five thousand rupees and the person "
        "is convicted for the first time, return or restoration shall result in community service. "
        "304. Snatching.—(1) Theft is snatching if the offender suddenly seizes movable property."
    )
    source = knowledge.add_source(
        title="Bharatiya Nyaya Sanhita, 2023 (BNS) — official full text",
        text=text,
        jurisdiction="IN",
        source_url="https://www.indiacode.nic.in/indiacode/bitstream/123456789/20062/1/a202345.pdf",
        as_of="2025-10-06",
        file_name="official-refresh:bns_2023",
        authority="official primary source",
        language="en",
        category="law",
    )

    from app.main import _retrieve_request

    results, coverage, task = _retrieve_request(
        "Under the Bharatiya Nyaya Sanhita, 2023 explain theft under Section 303(1) "
        "and punishment under Section 303(2)",
        "IN",
        5,
    )

    assert task == "legal_research"
    assert coverage[0]["status"] == "retrieved"
    assert results
    assert results[0]["id"] == source["id"]
    assert results[0]["provision_matches"] >= 1
    assert "303. Theft" in results[0]["content"]
    assert "three years" in results[0]["content"]
    assert "community service" in results[0]["content"]
    assert "304. Snatching" not in results[0]["content"]
