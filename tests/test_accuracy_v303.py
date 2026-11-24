"""Regression tests for the 3.0.3 accuracy fixes."""
from app import llm
from app.ambiguity import clarification_for


# --- task routing ---------------------------------------------------------
def test_common_words_do_not_trigger_legal_research():
    assert llm.classify_task("What is the fact that practical exact results matter?") == "general"
    assert llm.classify_task("Explain how nitrogen cycles through soil") == "general"
    assert llm.classify_task("Act as a friendly tutor and explain photosynthesis") == "general"
    assert llm.classify_task("Where can I catch a taxi in the city?") == "general"


def test_statute_references_still_route_to_legal_research():
    assert llm.classify_task("What does Section 66A of the IT Act say?") == "legal_research"
    assert llm.classify_task("Explain the Companies Act, 2013 in brief") == "legal_research"
    assert llm.classify_task("Is this contract illegal?") == "legal_research"
    assert llm.classify_task("What do the courts say about privacy?") == "legal_research"


def test_tax_short_keywords_use_whole_tokens():
    assert llm.classify_task("When is the ITR deadline?") == "ca_tax"
    assert llm.classify_task("How is TDS deducted on salary?") == "ca_tax"


# --- context fitting ------------------------------------------------------
def test_fit_context_keeps_whole_sources_and_reports_count():
    entries = ["[S1] " + "a" * 1500, "[S2] " + "b" * 1500, "[S3] " + "c" * 1500]
    text, included = llm.fit_context(entries, limit=3500)
    assert included == 2
    assert "[S3]" not in text and "[S2]" in text
    assert len(text) <= 3500


def test_fit_context_marks_a_partial_last_source():
    entries = ["[S1] " + "a" * 1500, "[S2] " + "b" * 3000]
    text, included = llm.fit_context(entries, limit=3000)
    assert included == 2
    assert text.endswith("[excerpt truncated]")
    assert len(text) <= 3000


def test_fit_context_always_keeps_first_source():
    text, included = llm.fit_context(["[S1] " + "x" * 9000], limit=2000)
    assert included == 1 and len(text) <= 2000


# --- citations ------------------------------------------------------------
def test_grouped_citation_labels_are_recognised():
    result = llm.validate_citations("Both apply [S1, S2]; see also [S3; S4].", ["S1", "S2", "S3"])
    assert result["cited"] == ["S1", "S2", "S3", "S4"]
    assert result["invalid"] == ["S4"]
    assert result["paragraphs_with_citations"] == 1


# --- provider adapters ----------------------------------------------------
def test_retry_delay_parses_compound_durations():
    class Response:
        headers = {"x-ratelimit-reset-tokens": "1m30.5s"}
        text = ""
    assert llm._retry_delay(Response()) == 65.0  # capped

    class Body:
        headers = {}
        text = '{"error":{"message":"Please try again in 2m5.5s."}}'
    assert llm._retry_delay(Body()) == 65.0

    class Millis:
        headers = {}
        text = "try again in 250ms"
    assert llm._retry_delay(Millis()) == 1.0


def test_ollama_strips_inline_reasoning(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": "<think>private reasoning</think>\n\nFinal answer."}}

    monkeypatch.setattr(llm.requests, "post", lambda url, json, timeout: Response())
    answer, _model, _finish = llm._ollama([{"role": "user", "content": "hi"}])
    assert answer == "Final answer."


# --- ambiguity ------------------------------------------------------------
def test_common_instrument_abbreviations_are_not_blocked():
    assert clarification_for("What is Section 420 IPC?", "IN") is None
    assert clarification_for("Explain Section 66A of the IT Act", "IN") is None
    assert clarification_for("Summarise 42 U.S.C. Section 1983") is None
    assert clarification_for("Does Section 4 of the lease agreement allow subletting?") is None


def test_bare_provision_with_generic_wording_is_still_blocked():
    result = clarification_for("Explain Article 21 in simple terms")
    assert result and result["code"] == "ambiguous_legal_provision"


# --- bundled data ---------------------------------------------------------
def test_every_bundled_and_registry_jurisdiction_is_a_selectable_code():
    import json
    from pathlib import Path
    app_dir = Path(__file__).resolve().parents[1] / "app"
    codes = {
        item["code"].upper()
        for group in json.loads((app_dir / "jurisdictions.json").read_text(encoding="utf-8"))["groups"]
        for item in group["items"]
    }
    bundled = json.loads((app_dir / "builtin_knowledge.json").read_text(encoding="utf-8"))
    registry = json.loads((app_dir / "sources_registry.json").read_text(encoding="utf-8"))["sources"]
    assert {r["jurisdiction"].upper() for r in bundled} <= codes
    assert {r["jurisdiction"].upper() for r in registry} <= codes


def test_reseeding_repairs_relabelled_bundled_digest(monkeypatch, tmp_path):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "relabel.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()
    with knowledge.connect() as c:
        c.execute("UPDATE sources SET jurisdiction='IN-DELHI' WHERE title LIKE 'Naz Foundation%'")
    knowledge.seed_builtin_knowledge()
    hits = knowledge.search("Naz Foundation section 377 Delhi High Court", 5, "IN", "legal_research")
    assert any("Naz Foundation" in h["title"] for h in hits)
