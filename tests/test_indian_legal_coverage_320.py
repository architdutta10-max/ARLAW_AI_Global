import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_indian_primary_law_records_and_official_sources_are_bundled(tmp_path, monkeypatch):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "indian-law.db")
    knowledge.init_db()
    assert knowledge.seed_builtin_knowledge() >= 10
    checks = [
        ("BNS Bharatiya Nyaya Sanhita 2023 criminal offences", "Bharatiya Nyaya Sanhita"),
        ("BNSS Bharatiya Nagarik Suraksha Sanhita criminal procedure", "Bharatiya Nagarik Suraksha"),
        ("BSA Bharatiya Sakshya Adhiniyam electronic evidence", "Bharatiya Sakshya"),
        ("DPDP Act Digital Personal Data Protection Act 2023", "Digital Personal Data Protection Act"),
        ("DPDP Rules GSR 846 commencement 2025", "Digital Personal Data Protection Rules"),
        ("DPDP GSR 843 commencement notification", "DPDP Act commencement notification"),
        ("Limitation Act 1963 Schedule Article 54", "Limitation Act, 1963"),
        ("Section 23 Indian Contract Act 1872 lawful consideration objects", "Indian Contract Act, 1872"),
        ("Income Tax Act 2025 Tax Year 2026-27", "Income-tax Act, 2025"),
        ("Income-tax Rules 2026 GSR 198", "Income-tax Rules, 2026"),
    ]
    for query, expected in checks:
        hits = knowledge.search(query, 8, "IN", "legal_research")
        assert any(expected in hit["title"] for hit in hits), (query, [x["title"] for x in hits])


def test_contract_section_22_is_not_conflated_with_section_23(tmp_path, monkeypatch):
    import app.knowledge as knowledge
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "contract.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()
    sec22 = knowledge.search("Section 22 Indian Contract Act unilateral mistake fact", 5, "IN", "legal_research")
    sec23 = knowledge.search("Section 23 Indian Contract Act unlawful consideration object", 5, "IN", "legal_research")
    assert sec22 and sec23
    assert any("Section 22" in x["content"] for x in sec22)
    assert any("Section 23" in x["content"] for x in sec23)


def test_dpdp_act_rules_and_commencement_are_separate_records():
    records = json.loads((ROOT / "app/builtin_knowledge.json").read_text(encoding="utf-8"))
    titles = {x["title"] for x in records}
    assert "India — Digital Personal Data Protection Act, 2023 — Act text (separate source)" in titles
    assert "India — Digital Personal Data Protection Rules, 2025 — G.S.R. 846(E) (separate source)" in titles
    assert "India — DPDP Act commencement notification — G.S.R. 843(E) (separate source)" in titles


def test_legal_source_refresh_uses_fixed_allowlist_and_is_not_startup_hook():
    script = (ROOT / "scripts/refresh_indian_legal_corpus.py").read_text(encoding="utf-8")
    assert "ALLOWED_HOSTS" in script
    assert "MAX_BYTES" in script
    assert "if __name__ == \"__main__\"" in script
    assert "refresh_indian_legal_corpus" not in (ROOT / "app/main.py").read_text(encoding="utf-8")


def test_huggingface_zero_shot_requires_candidate_labels(monkeypatch):
    from app.optional_models import run_hf_text
    import pytest
    with pytest.raises(ValueError, match="candidate_labels"):
        run_hf_text("A contract dispute", task="zero-shot-classification", model="test/model")


def test_huggingface_model_allowlist_is_enforced(monkeypatch):
    from app.optional_models import run_hf_text
    import pytest
    monkeypatch.setenv("ARLAW_HF_ALLOWED_MODELS", "approved/model")
    with pytest.raises(ValueError, match="not in ARLAW_HF_ALLOWED_MODELS"):
        run_hf_text("A legal document", model="unapproved/model")
