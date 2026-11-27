from app.knowledge import split_text

def test_empty(): assert split_text("") == []
def test_short(): assert split_text("short text") == ["short text"]
def test_long(): assert len(split_text("x"*3000,size=1000,overlap=100)) >= 3


def test_builtin_knowledge_seed_is_idempotent(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "seed-test.db")
    knowledge.init_db()
    first = knowledge.seed_builtin_knowledge()
    second = knowledge.seed_builtin_knowledge()
    assert first >= 15
    assert second == 0
    results = knowledge.search("Mabo native title High Court Australia", top_k=5, jurisdiction="AU")
    assert any("Mabo" in row["title"] for row in results)


def test_bundled_sources_are_topic_classified_and_separated(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "topic-test.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()
    legal = knowledge.search("Article 14 equality Constitution India", 8, "IN", "legal_research")
    assert legal
    assert all(row["category"] in {"law", "general"} for row in legal)
    assert not any("shortage monitoring framework" in row["title"].lower() for row in legal)
    economy = knowledge.search("food agriculture shortage monitoring indicators", 8, "GLOBAL", "finance_tax")
    assert economy
    assert all(row["category"] in {"economy", "general"} for row in economy)


def test_search_does_not_fall_back_to_an_unrelated_jurisdiction(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "jurisdiction-test.db")
    knowledge.init_db()
    knowledge.add_source("US constitutional equality", "United States constitutional equal protection and judicial review", "US", authority="secondary")
    assert knowledge.search("constitutional equality judicial review", 5, "IN", "legal_research") == []


def test_legacy_database_migration_adds_and_backfills_categories(monkeypatch, tmp_path):
    import sqlite3
    import app.knowledge as knowledge
    db = tmp_path / "legacy.db"
    monkeypatch.setattr(knowledge, "DB_PATH", db)
    with sqlite3.connect(db) as c:
        c.execute("CREATE TABLE sources (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, jurisdiction TEXT NOT NULL DEFAULT 'GLOBAL', source_url TEXT DEFAULT '', as_of TEXT DEFAULT '', file_name TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP, authority TEXT DEFAULT 'secondary', language TEXT DEFAULT 'en')")
        c.execute("CREATE VIRTUAL TABLE chunks USING fts5(source_id UNINDEXED, chunk_no UNINDEXED, content, tokenize='unicode61')")
        c.execute("INSERT INTO sources(title,jurisdiction,file_name,authority,language) VALUES(?,?,?,?,?)", ("Food, agriculture and food-shortage monitoring framework", "GLOBAL", "bundled-curated-digest", "secondary", "en"))
        c.execute("INSERT INTO chunks(source_id,chunk_no,content) VALUES(1,0,?)", ("food shortage monitoring indicators agriculture",))
    knowledge.init_db()
    with knowledge.connect() as c:
        category = c.execute("SELECT category FROM sources WHERE id=1").fetchone()[0]
    assert category == "economy"

def test_legal_search_ranks_declared_official_authority_above_secondary(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "authority-test.db")
    knowledge.init_db()
    text = "constitutional equality judicial review fundamental rights"
    knowledge.add_source("Constitutional equality official text", text, "IN", authority="official")
    knowledge.add_source("Constitutional equality secondary note", text, "IN", authority="secondary")
    results = knowledge.search("constitutional equality judicial review", 5, "IN", "legal_research")
    assert len(results) == 2
    assert results[0]["authority"] == "official"
    assert results[0]["authority_priority"] > results[1]["authority_priority"]


def test_legal_search_excludes_global_and_international_fallback(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "strict-legal-test.db")
    knowledge.init_db()
    text = "constitutional equality judicial review fundamental rights"
    knowledge.add_source("India constitutional material", text, "IN", authority="official")
    knowledge.add_source("Global constitutional material", text, "GLOBAL", authority="official")
    knowledge.add_source("International constitutional material", text, "INTL", authority="official")
    results = knowledge.search("constitutional equality judicial review", 10, "IN", "legal_research")
    assert results
    assert all(row["jurisdiction"] == "IN" for row in results)
    assert all(row["jurisdiction_relation"] == "exact" for row in results)


def test_nonlegal_search_labels_global_and_international_context(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "context-test.db")
    knowledge.init_db()
    text = "food security agricultural supply economic indicators"
    knowledge.add_source("India food security indicators", text, "IN", authority="official")
    knowledge.add_source("Global food security indicators", text, "GLOBAL", authority="official")
    knowledge.add_source("International food security indicators", text, "INTL", authority="official")
    results = knowledge.search("food security agricultural indicators", 10, "IN", "finance_tax")
    relations = {row["jurisdiction_relation"] for row in results}
    assert "exact" in relations
    assert "global_context" in relations
    assert "international_context" in relations

def test_legal_sql_filter_precedes_candidate_limit(monkeypatch, tmp_path):
    import app.knowledge as knowledge

    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "sql-filter-test.db")
    knowledge.init_db()

    text = "constitutional equality judicial review fundamental rights"

    # Many GLOBAL matches must not crowd out the exact domestic source.
    for index in range(75):
        knowledge.add_source(
            f"Global constitutional material {index}",
            text,
            "GLOBAL",
            authority="official"
        )

    knowledge.add_source(
        "India constitutional equality source",
        text,
        "IN",
        authority="official"
    )

    results = knowledge.search(
        "constitutional equality judicial review",
        1,
        "IN",
        "legal_research"
    )

    assert results
    assert results[0]["jurisdiction"] == "IN"
    assert results[0]["title"] == "India constitutional equality source"


def test_us_first_amendment_query_does_not_return_unrelated_case_digests(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "first-amendment-test.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()
    results = knowledge.search(
        "Explain the First Amendment of the United States Constitution and cite authoritative legal sources.",
        6, "US", "legal_research"
    )
    # The bundled US corpus has case digests, but no primary First Amendment text.
    # Do not cite unrelated cases as if they support this specific question.
    assert results == []


def test_india_article_21_query_still_retrieves_primary_material(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "article-21-test.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()
    results = knowledge.search(
        "Explain Article 21 of the Constitution of India and cite authoritative legal sources.",
        6, "IN", "legal_research"
    )
    assert results
    assert any(row["authority"] == "official primary source" for row in results)
    assert any(
        "No person shall be deprived of his life or personal liberty" in row["content"]
        for row in results
    )



def test_generic_homepage_is_not_accepted_as_document_source():
    from app.knowledge import _specific_source_url
    assert _specific_source_url("https://www.sci.gov.in/") == ""
    assert _specific_source_url("https://api.sci.gov.in/jonew/judis/5154.pdf") == "https://api.sci.gov.in/jonew/judis/5154.pdf"


def test_document_level_source_url_is_preserved():
    from app.knowledge import _specific_source_url
    url = "https://api.sci.gov.in/jonew/judis/5154.pdf"
    assert _specific_source_url(url) == url


def test_long_structured_article_21_prompt_retrieves_primary_sources(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "article-21-long-prompt.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()
    question = (
        "Explain Article 21 of the Constitution of India. Requirements: quote or accurately "
        "paraphrase the relevant constitutional provision. Explain the legal principles "
        "established in Maneka Gandhi v. Union of India (1978). Distinguish the original "
        "judgment from later interpretations. Cite primary legal sources with direct links "
        "and relevant paragraph or page references wherever available. Clearly distinguish "
        "binding law from secondary commentary. Do not invent case citations or quotations. "
        "Include the date or edition of the legal materials used."
    )
    results = knowledge.search(question, 5, "IN", "legal_research")
    titles = [row["title"] for row in results]
    assert any("Maneka Gandhi" in title and "official judgment" in title for title in titles)
    assert any("Constitution of India" in title and "official primary text" in title for title in titles)
    assert any(
        "No person shall be deprived of his life or personal liberty" in row["content"]
        for row in results
    )


def test_article_21_retrieval_prefers_the_actual_provision_passage(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "article-21-precision.db")
    knowledge.init_db()
    knowledge.add_source(
        "Constitution of India (2026 edition) - official primary text",
        "171. Composition of the Legislative Council. This provision includes 21-2-2002 "
        "as a commencement date and territorial constituencies.",
        "IN", authority="official primary source", category="law"
    )
    knowledge.add_source(
        "Constitution of India (2026 edition) - official primary text",
        "21. Protection of life and personal liberty. —No person shall be deprived of "
        "his life or personal liberty except according to procedure established by law.",
        "IN", authority="official primary source", category="law"
    )
    results = knowledge.search("Explain Article 21 of the Constitution of India.", 5, "IN", "legal_research")
    assert results
    assert "No person shall be deprived" in results[0]["content"]


def test_first_amendment_query_does_not_return_unrelated_constitutional_digest(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "first-amendment-precision.db")
    knowledge.init_db()
    knowledge.add_source(
        "Obergefell v. Hodges — case digest",
        "The Supreme Court held that the Fourteenth Amendment requires states to "
        "license and recognize marriages between two people of the same sex.",
        "US", authority="secondary", category="law"
    )
    assert knowledge.search("What is the First Amendment of the United States Constitution?", 5, "US", "legal_research") == []


def test_builtin_seed_refreshes_changed_bundled_text_and_metadata(monkeypatch, tmp_path):
    import json
    import app.knowledge as knowledge

    app_dir = tmp_path / "app"
    app_dir.mkdir()
    fake_module = app_dir / "knowledge.py"
    fake_module.write_text("# test module path", encoding="utf-8")
    source_file = app_dir / "builtin_knowledge.json"
    monkeypatch.setattr(knowledge, "__file__", str(fake_module))
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "refresh.db")

    def write_record(text, authority="secondary", jurisdiction="IN"):
        source_file.write_text(json.dumps([{
            "title": "Seed refresh regression source",
            "text": text,
            "jurisdiction": jurisdiction,
            "authority": authority,
            "language": "en",
            "as_of": "2026-11-25",
            "source_url": "https://example.org/legal/document.pdf",
            "file_name": "bundled-curated-digest",
            "category": "law",
        }]), encoding="utf-8")

    knowledge.init_db()
    write_record("Original statutory text about a test provision.")
    assert knowledge.seed_builtin_knowledge() == 1
    write_record("Corrected statutory text about the test provision and its scope.", "official secondary", "UK")
    assert knowledge.seed_builtin_knowledge() == 0

    with knowledge.connect() as c:
        source = c.execute(
            "SELECT jurisdiction,authority,source_url FROM sources WHERE title=?",
            ("Seed refresh regression source",),
        ).fetchone()
        chunks = [r[0] for r in c.execute(
            "SELECT content FROM chunks WHERE source_id=(SELECT id FROM sources WHERE title=?) ORDER BY chunk_no",
            ("Seed refresh regression source",),
        )]
    assert source["jurisdiction"] == "UK"
    assert source["authority"] == "official secondary"
    assert source["source_url"] == "https://example.org/legal/document.pdf"
    assert "Corrected statutory text" in " ".join(chunks)
    assert "Original statutory text" not in " ".join(chunks)


def test_builtin_seed_does_not_overwrite_user_uploaded_same_title(monkeypatch, tmp_path):
    import json
    import app.knowledge as knowledge

    app_dir = tmp_path / "app"
    app_dir.mkdir()
    fake_module = app_dir / "knowledge.py"
    fake_module.write_text("# test module path", encoding="utf-8")
    (app_dir / "builtin_knowledge.json").write_text(json.dumps([{
        "title": "User-owned same title", "text": "Bundled replacement text",
        "jurisdiction": "IN", "authority": "official", "language": "en",
        "file_name": "bundled-curated-digest", "category": "law",
    }]), encoding="utf-8")
    monkeypatch.setattr(knowledge, "__file__", str(fake_module))
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "user-source.db")
    knowledge.init_db()
    knowledge.add_source("User-owned same title", "User uploaded original source text", "IN", file_name="user-upload.pdf")
    assert knowledge.seed_builtin_knowledge() == 0
    with knowledge.connect() as c:
        row = c.execute("SELECT file_name FROM sources WHERE title=?", ("User-owned same title",)).fetchone()
        text = c.execute("SELECT content FROM chunks WHERE source_id=1").fetchone()[0]
    assert row["file_name"] == "user-upload.pdf"
    assert text == "User uploaded original source text"


def test_eu_gdpr_digest_is_retrievable_under_eu_jurisdiction(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "eu-gdpr.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()
    results = knowledge.search(
        "EU GDPR Regulation 2016/679 territorial scope lawful bases data subject rights",
        5, "EU", "legal_research"
    )
    assert results
    assert any("GDPR Regulation (EU) 2016/679" in row["title"] for row in results)


def test_eu_dual_use_digest_is_retrievable_under_eu_jurisdiction(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "eu-dual-use.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()
    results = knowledge.search(
        "EU Dual-Use Regulation 2021/821 export control Annex I authorisation",
        5, "EU", "legal_research"
    )
    assert results
    assert any("Dual-Use Regulation (EU) 2021/821" in row["title"] for row in results)


def test_corporate_fraud_fact_pattern_retrieves_india_fraud_digest_first(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "corporate-fraud-retrieval.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()
    results = knowledge.search(
        "A company conceals financial losses, falsifies accounts and transfers assets for personal benefit.",
        3, "IN", "legal_research"
    )
    assert results
    assert "corporate fraud" in results[0]["title"].lower()


def test_named_bns_section_excludes_same_numbered_constitution_provision(monkeypatch, tmp_path):
    import app.knowledge as knowledge

    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "bns-scope.db")
    knowledge.init_db()

    knowledge.add_source(
        title="Bharatiya Nyaya Sanhita, 2023 (BNS) ? official full text",
        text="Section 308. Extortion. Whoever intentionally puts any person in fear of injury "
             "and thereby dishonestly induces delivery of property commits extortion.",
        jurisdiction="IN",
        authority="official primary source",
        category="law",
    )
    knowledge.add_source(
        title="Constitution of India ? official primary text",
        text="Section 308. Interpretation. This unrelated constitutional provision mentions "
             "extortion, fear of injury, and delivery of property.",
        jurisdiction="IN",
        authority="official primary source",
        category="law",
    )

    results = knowledge.search(
        "Under BNS Section 308 explain extortion, fear of injury and delivery of property",
        top_k=8,
        jurisdiction="IN",
        task="legal_research",
    )

    assert results
    assert all("bharatiya nyaya sanhita" in row["title"].lower() for row in results)


def test_named_contract_act_section_excludes_same_numbered_constitution_provision(monkeypatch, tmp_path):
    import app.knowledge as knowledge

    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "contract-scope.db")
    knowledge.init_db()

    knowledge.add_source(
        title="Indian Contract Act, 1872 ? official full text",
        text="Section 10. What agreements are contracts. All agreements are contracts "
             "if made by free consent of parties competent to contract, "
             "for lawful consideration and with a lawful object.",
        jurisdiction="IN",
        authority="official primary source",
        category="law",
    )
    knowledge.add_source(
        title="Constitution of India ? official primary text",
        text="Section 10. Continuance of rights. This unrelated provision discusses "
             "agreements, consent, competent parties, lawful consideration and object.",
        jurisdiction="IN",
        authority="official primary source",
        category="law",
    )

    results = knowledge.search(
        "Indian Contract Act 1872 Section 10 agreements free consent competent parties "
        "lawful consideration lawful object",
        top_k=8,
        jurisdiction="IN",
        task="legal_research",
    )

    assert results
    assert all("indian contract act" in row["title"].lower() for row in results)
