from pathlib import Path

from app.llm import _high_risk_legal_number_warning, _messages, classify_task

ROOT = Path(__file__).resolve().parents[1]


def test_legal_article_question_with_finance_word_stays_legal():
    assert classify_task("Explain Article 21 and its legal implications for tax policy") == "legal_research"


def test_document_review_without_sources_gets_evidence_warning():
    payload = _messages(
        [{"role": "user", "content": "Review this agreement for legal risks."}],
        context="",
        task="document_review",
    )
    prompt = "\n".join(item["content"] for item in payload).lower()
    assert "no sources were retrieved" in prompt
    assert "do not cite specific case names" in prompt


def test_document_review_high_risk_numbers_are_flagged():
    assert _high_risk_legal_number_warning(
        "The agreement says a penalty of ₹5 lakh applies after 30 days.",
        "document_review",
    )


def test_selective_chat_delete_has_confirmation_and_persists_removal():
    js = (ROOT / "app/static/app.js").read_text(encoding="utf-8")
    css = (ROOT / "app/static/style.css").read_text(encoding="utf-8")
    assert "function deleteConversation(id)" in js
    assert "window.confirm('Permanently delete this conversation?')" in js
    assert "conversations=conversations.filter(x=>x.id!==id);\n persistHistory();" in js
    assert "aria-label','Delete conversation:" in js
    assert ".history-delete:focus-visible" in css


def test_static_asset_cache_version_matches_release():
    html = (ROOT / "app/static/index.html").read_text(encoding="utf-8")
    assert "style.css?v=3.1.3" in html
    assert "app.js?v=3.1.3" in html
