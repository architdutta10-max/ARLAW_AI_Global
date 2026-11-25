from app import knowledge
from app import main


def test_global_article_21_request_routes_to_india_primary_source(monkeypatch, tmp_path):
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "routing-article21.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()

    question = (
        "Explain Article 21 of the Constitution of India. Identify relevant Supreme Court "
        "judgments and cite official legal sources."
    )
    hits, coverage, task = main._retrieve_request(question, "GLOBAL", 5)

    assert task == "legal_research"
    assert coverage[0]["jurisdictions_searched"] == ["IN"]
    assert coverage[0]["jurisdictions_with_sources"] == ["IN"]
    assert any(
        "No person shall be deprived of his life or personal liberty" in hit["content"]
        for hit in hits
    )


def test_multi_question_global_prompt_routes_each_question_separately(monkeypatch):
    calls = []

    def fake_search(query, top_k, jurisdiction, task):
        calls.append((query, jurisdiction, task))
        return []

    monkeypatch.setattr(main, "search", fake_search)
    question = """QUESTION 1 — Constitutional Law: India
An Indian citizen challenges Article 21 of the Constitution of India.

QUESTION 2 — Privacy: Germany, UK and United States
A company processes data in Germany, the United Kingdom and the United States under GDPR.

QUESTION 3 — Competition: India and EU
Explain cartelisation under Indian and European Union competition law."""

    hits, coverage, task = main._retrieve_request(question, "GLOBAL", 5)

    assert hits == []
    assert task == "legal_research"
    assert [row["jurisdictions_searched"] for row in coverage] == [
        ["IN"], ["DE", "UK", "US", "EU"], ["IN", "EU"]
    ]
    assert {call[1] for call in calls} == {"IN", "DE", "UK", "US", "EU"}
    assert all(call[2] == "legal_research" for call in calls)


def test_explicit_india_selection_is_not_overridden_by_other_country_mentions(monkeypatch):
    calls = []

    def fake_search(query, top_k, jurisdiction, task):
        calls.append(jurisdiction)
        return []

    monkeypatch.setattr(main, "search", fake_search)
    main._retrieve_request(
        "Compare Indian law with United States law on privacy.", "IN", 5
    )
    assert calls == ["IN"]


def test_economic_keywords_do_not_mask_explicit_competition_law_question():
    question = (
        "Explain the economic effects, cartelisation, penalties and legal framework "
        "in India and the European Union."
    )
    assert main._section_task(question) == "legal_research"


def test_numbered_question_split_keeps_all_question_bodies():
    question = """QUESTION 1 — India
First question body.

QUESTION 2 — Singapore
Second question body."""
    sections = main._split_research_sections(question)
    assert len(sections) == 2
    assert sections[0]["number"] == 1
    assert sections[0]["text"] == "First question body."
    assert sections[1]["number"] == 2
    assert sections[1]["text"] == "Second question body."


def test_chat_api_does_not_abstain_for_india_article_21_when_global_selected(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "api-article21.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()

    def fake_generate(messages, context, source_labels):
        assert "No person shall be deprived of his life or personal liberty" in context
        assert source_labels
        return (
            "Article 21 source retrieved [S1]",
            None,
            {
                "task": "legal_research",
                "quality_warning": None,
                "citation_validation": {"status": "test_stub"},
                "quality": None,
                "incomplete": False,
            },
        )

    monkeypatch.setattr(main, "generate", fake_generate)
    with TestClient(main.app) as client:
        response = client.post(
            "/api/chat",
            json={
                "messages": [{
                    "role": "user",
                    "content": "Explain Article 21 of the Constitution of India and cite official sources.",
                }],
                "jurisdiction": "GLOBAL",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "could not retrieve a jurisdiction-matched" not in data["answer"].lower()
    assert data["retrieval_coverage"][0]["jurisdictions_searched"] == ["IN"]
    assert data["citations"]


def test_question_mark_heading_compatibility_after_console_encoding():
    question = (
        "QUESTION 1 ? Constitutional Law: India\n"
        "Explain Article 21.\n\n"
        "QUESTION 2 ? Privacy: Germany\n"
        "Explain GDPR."
    )

    sections = main._split_research_sections(question)

    assert len(sections) == 2
    assert [section["number"] for section in sections] == [1, 2]
    assert sections[0]["title"] == "Constitutional Law: India"
    assert sections[1]["title"] == "Privacy: Germany"


def test_ten_question_prompt_routes_each_section_independently(monkeypatch):
    calls = []

    def fake_search(query, top_k, jurisdiction, task):
        calls.append((query, jurisdiction, task))
        return []

    monkeypatch.setattr(main, "search", fake_search)

    dash = chr(0x2014)
    headings = [
        ("Constitutional Law: India", "Explain Article 21 of the Constitution of India."),
        ("Privacy: Germany, United Kingdom and United States", "Explain privacy laws."),
        ("Criminal Law: India, United Kingdom and United States", "Compare criminal and civil burdens of proof."),
        ("Civil Law: India", "Explain breach of contract under Indian law."),
        ("Competition Law: India and European Union", "Explain cartelisation."),
        ("International Trade: India", "Explain international sanctions and export-control risks."),
        ("Legal Research: India", "Explain Article 21 and Supreme Court judgments."),
        ("Financial Regulation: India", "Explain RBI digital lending requirements."),
        ("Contract Law: India and Singapore", "Explain governing law and jurisdiction."),
        ("Hallucination Test: India", "Verify whether a fictional Supreme Court judgment exists."),
    ]

    prompt = "\n\n".join(
        f"QUESTION {number} {dash} {title}\n{body}"
        for number, (title, body) in enumerate(headings, 1)
    )

    hits, coverage, task = main._retrieve_request(prompt, "GLOBAL", 5)

    assert hits == []
    assert task == "legal_research"
    assert len(coverage) == 10
    assert [item["question"] for item in coverage] == list(range(1, 11))
    assert len(calls) > 10
    assert all(call[2] == "legal_research" for call in calls)

    assert coverage[0]["jurisdictions_searched"] == ["IN"]
    assert coverage[1]["jurisdictions_searched"] == ["DE", "UK", "US"]
    assert coverage[4]["jurisdictions_searched"] == ["IN", "EU"]
    assert coverage[8]["jurisdictions_searched"] == ["IN", "SG"]


def test_international_trade_sanctions_are_classified_as_legal_research():
    from app import main

    question = (
        "International Trade: India\\n"
        "Explain international sanctions and export-control risks."
    )
    assert main._section_task(question) == "legal_research"


def test_trade_regulatory_terms_are_recognised_as_legal_topics():
    from app import main

    questions = [
        "Explain export controls under applicable law.",
        "Explain customs law and import-export restrictions.",
        "Explain trade compliance and embargoes.",
        "Explain tariff rules under international trade law.",
    ]

    for question in questions:
        assert main._section_task(question) == "legal_research", question


def test_markdown_numbered_headings_split_each_requested_section():
    question = """**1. Indian Constitutional Law — Article 21**
Explain Article 21 of the Constitution of India.

**2. International Privacy and Data Protection**
Compare India, Germany, the United Kingdom and the United States.

**3. Corporate and Economic Law**
Explain corporate fraud and international approaches.

**4. Competition Law**
Explain cartels in India and the European Union.

**5. International Trade and Sanctions**
Explain trade controls in India, Germany and Singapore."""

    sections = main._split_research_sections(question)

    assert len(sections) == 5
    assert [section["number"] for section in sections] == [1, 2, 3, 4, 5]
    assert "Article 21" in sections[0]["title"]
    assert "Germany" in sections[1]["text"]
    assert "international approaches" in sections[2]["text"]
    assert "Singapore" in sections[4]["text"]


def test_international_approaches_routes_to_intl(monkeypatch):
    calls = []

    def fake_search(query, top_k, jurisdiction, task):
        calls.append(jurisdiction)
        return []

    monkeypatch.setattr(main, "search", fake_search)
    main._retrieve_request(
        "Explain corporate fraud and compare Indian law with international approaches.",
        "GLOBAL", 5,
    )
    assert calls == ["IN", "INTL"]
