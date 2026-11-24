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
