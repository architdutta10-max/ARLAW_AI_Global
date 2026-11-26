import hashlib
import sqlite3

import pytest

from app import legal_governance as gov
from app.legal_evidence import verify_exact_quote


def _temporary_governance_db(tmp_path, monkeypatch):
    db = tmp_path / "governance.db"
    monkeypatch.setattr(gov, "DB_PATH", db)
    with sqlite3.connect(db) as c:
        c.execute("""CREATE TABLE sources (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL,
            jurisdiction TEXT NOT NULL DEFAULT 'GLOBAL'
        )""")
    gov.init_governance_db()
    return db


def test_manifest_covers_all_52_selector_entries_and_marks_gaps(tmp_path, monkeypatch):
    _temporary_governance_db(tmp_path, monkeypatch)
    report = gov.coverage_report()
    assert report["selector_count"] == 52
    assert report["verified_legal_coverage_count"] == 0
    assert report["unverified_registry_candidate_count"] == 12
    assert report["no_registered_source_count"] == 40
    assert report["production_coverage_certified"] is False


def test_document_version_hash_provision_and_temporal_gate(tmp_path, monkeypatch):
    _temporary_governance_db(tmp_path, monkeypatch)
    document_id = gov.register_document(
        document_key="IN:TEST:ACT", jurisdiction_code="IN", title="Test Act",
        document_type="statute", official_url="https://example.invalid/act",
        authority_tier="unverified", verification_status="unverified",
    )
    payload = b"Section 1. Commencement is on 2026-01-01."
    version_id, digest = gov.record_document_version(
        document_id, payload, version_label="test-v1",
        effective_from="2026-01-01", status="unverified",
    )
    assert digest == hashlib.sha256(payload).hexdigest()
    provision_id = gov.add_provision(version_id, "section-1", payload.decode(), heading="Commencement")
    assert provision_id > 0
    assessment = gov.assess_temporal_applicability(version_id, "2026-02-01")
    assert assessment["status"] == "date_range_matches_but_version_unverified"
    assert assessment["legal_applicability_certified"] is False


def test_temporal_gate_does_not_infer_effective_date(tmp_path, monkeypatch):
    _temporary_governance_db(tmp_path, monkeypatch)
    document_id = gov.register_document(
        document_key="IN:TEST:UNKNOWN", jurisdiction_code="IN", title="Unknown Dates Act",
        document_type="statute", official_url="", authority_tier="unverified",
    )
    version_id, _ = gov.record_document_version(document_id, b"Text", status="unverified")
    assert gov.assess_temporal_applicability(version_id, "2025-01-01")["status"] == "unknown_missing_effective_from"


def test_hierarchy_requires_existing_parent_and_does_not_certify_coverage(tmp_path, monkeypatch):
    _temporary_governance_db(tmp_path, monkeypatch)
    with pytest.raises(ValueError):
        gov.register_jurisdiction_node(
            "US:CA", "California", parent_code="MISSING", node_type="state",
            territorial_scope="US state",
        )
    gov.register_jurisdiction_node(
        "US:CA", "California", parent_code="US", node_type="state",
        territorial_scope="US state; source coverage unverified",
    )
    with sqlite3.connect(gov.DB_PATH) as c:
        row = c.execute("SELECT parent_code,coverage_status FROM jurisdiction_nodes WHERE code='US:CA'").fetchone()
    assert row == ("US", "unverified")


def test_exact_quote_checker_only_confirms_literal_presence():
    result = verify_exact_quote(
        "  The Court held that the appeal is allowed. ",
        [{"id": 4, "title": "Judgment", "jurisdiction": "IN",
          "content": "The Court held that the appeal is allowed."}],
    )
    assert result["exact_text_match"] is True
    assert result["semantic_support_verified"] is False
    assert result["source_authenticity_verified"] is False
    missing = verify_exact_quote("different quote", [{"content": "source text"}])
    assert missing["exact_text_match"] is False


def test_legal_coverage_api_reports_noncertified_status():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        response = client.get("/api/legal/coverage")
        one = client.get("/api/legal/jurisdictions/IN/sources")
        missing = client.get("/api/legal/jurisdictions/XX/sources")
    assert response.status_code == 200
    assert response.json()["selector_count"] == 52
    assert response.json()["production_coverage_certified"] is False
    assert one.status_code == 200 and one.json()["code"] == "IN"
    assert missing.status_code == 404


def test_invalid_or_reversed_effective_dates_are_rejected(tmp_path, monkeypatch):
    _temporary_governance_db(tmp_path, monkeypatch)
    document_id = gov.register_document(
        document_key="IN:TEST:BADDATE", jurisdiction_code="IN", title="Date Test",
        document_type="statute", official_url="", authority_tier="unverified",
    )
    with pytest.raises(ValueError):
        gov.record_document_version(document_id, b"text", effective_from="not-a-date")
    with pytest.raises(ValueError):
        gov.record_document_version(
            document_id, b"text", effective_from="2026-02-01", effective_to="2026-01-01"
        )


def test_release_gate_blocks_uncertified_global_release(monkeypatch):
    import runpy
    monkeypatch.delenv("ARLAW_PERSISTENCE_VERIFIED", raising=False)
    monkeypatch.delenv("ARLAW_SECURITY_AUDIT_PASSED", raising=False)
    monkeypatch.delenv("ARLAW_HUMAN_REVIEW_APPROVED", raising=False)
    gate = runpy.run_path(str(__import__("pathlib").Path(__file__).resolve().parents[1] / "scripts" / "legal_release_gate.py"))
    result = gate["evaluate"]()
    assert result["release_ready"] is False
    assert result["verified_legal_coverage"] == 0
    assert result["checks"]["selector_source_and_benchmark_code_sets_match_without_duplicates"] is True
    assert all(
        value is False for key, value in result["checks"].items()
        if key != "selector_source_and_benchmark_code_sets_match_without_duplicates"
    )



def test_verified_status_cannot_be_self_declared(tmp_path, monkeypatch):
    _temporary_governance_db(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="authenticated review workflow"):
        gov.register_document(
            document_key="IN:SELF:VERIFIED", jurisdiction_code="IN", title="Self Verified",
            document_type="statute", official_url="", authority_tier="unverified",
            verification_status="verified",
        )
    document_id = gov.register_document(
        document_key="IN:SELF:UNVERIFIED", jurisdiction_code="IN", title="Unverified",
        document_type="statute", official_url="", authority_tier="unverified",
    )
    with pytest.raises(ValueError, match="authenticated review workflow"):
        gov.record_document_version(document_id, b"text", status="verified")


def test_every_connection_enables_sqlite_foreign_keys(tmp_path, monkeypatch):
    _temporary_governance_db(tmp_path, monkeypatch)
    with gov._connect() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO legal_document_versions(document_id,content_sha256) VALUES(?,?)",
                (999999, "a" * 64),
            )


def test_hierarchy_cycle_is_rejected(tmp_path, monkeypatch):
    _temporary_governance_db(tmp_path, monkeypatch)
    gov.register_jurisdiction_node(
        "TEST:A", "A", parent_code=None, node_type="national", territorial_scope="test"
    )
    gov.register_jurisdiction_node(
        "TEST:B", "B", parent_code="TEST:A", node_type="state", territorial_scope="test"
    )
    with pytest.raises(ValueError, match="cycle"):
        gov.register_jurisdiction_node(
            "TEST:A", "A", parent_code="TEST:B", node_type="national", territorial_scope="test"
        )


def test_relation_metadata_is_validated(tmp_path, monkeypatch):
    _temporary_governance_db(tmp_path, monkeypatch)
    doc = gov.register_document(
        document_key="IN:REL:ACT", jurisdiction_code="IN", title="Relation Act",
        document_type="statute", official_url="", authority_tier="unverified",
    )
    v1, _ = gov.record_document_version(doc, b"v1")
    v2, _ = gov.record_document_version(doc, b"v2")
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        gov.record_version_relation(v1, v2, "amends", effective_on="not-a-date")
    with pytest.raises(ValueError, match="self"):
        gov.record_version_relation(v1, v1, "amends")
    with pytest.raises(ValueError, match="authenticated review workflow"):
        gov.record_version_relation(v1, v2, "amends", verification_status="verified")
    with pytest.raises(sqlite3.IntegrityError):
        gov.record_version_relation(999999, v2, "amends")


def test_ingestion_metadata_is_validated(tmp_path, monkeypatch):
    _temporary_governance_db(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="status"):
        gov.record_ingestion_run(source_url="https://example.test", status="verified")
    with pytest.raises(ValueError, match="source_url"):
        gov.record_ingestion_run(source_url="", status="started")
    with pytest.raises(ValueError, match="negative"):
        gov.record_ingestion_run(
            source_url="https://example.test", status="completed", extracted_characters=-1
        )


def test_release_gate_rejects_env_var_bypass(monkeypatch, tmp_path):
    import runpy
    gate_path = __import__("pathlib").Path(__file__).resolve().parents[1] / "scripts" / "legal_release_gate.py"
    monkeypatch.setenv("ARLAW_PERSISTENCE_VERIFIED", "true")
    monkeypatch.setenv("ARLAW_SECURITY_AUDIT_PASSED", "true")
    monkeypatch.setenv("ARLAW_HUMAN_REVIEW_APPROVED", "true")
    gate = runpy.run_path(str(gate_path))
    result = gate["evaluate"]()
    assert result["checks"]["persistent_hosted_storage_verified"] is False
    assert result["checks"]["independent_security_audit_passed"] is False
    assert result["checks"]["qualified_human_legal_review_approved"] is False


def test_evidence_artifact_hash_scope_and_path_are_checked(tmp_path, monkeypatch):
    import hashlib
    import runpy
    from datetime import date
    from pathlib import Path
    gate_path = Path(__file__).resolve().parents[1] / "scripts" / "legal_release_gate.py"
    gate = runpy.run_path(str(gate_path))
    monkeypatch.setitem(gate["_evidence_check"].__globals__, "ROOT", tmp_path)
    evidence_dir = tmp_path / "release_evidence"
    evidence_dir.mkdir()
    report = tmp_path / "security-report.txt"
    report.write_text("audit completed", encoding="utf-8")
    meta = {
        "status": "passed", "reviewer": "Reviewer A",
        "reviewer_qualification": "Qualified security auditor",
        "reviewed_at": date.today().isoformat(), "scope_version": "3.3.0",
        "artifact_path": "security-report.txt",
        "artifact_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
    }
    (evidence_dir / "security_audit.json").write_text(
        __import__("json").dumps(meta), encoding="utf-8"
    )
    assert gate["_evidence_check"]("security_audit", "3.3.0") is True
    report.write_text("tampered", encoding="utf-8")
    assert gate["_evidence_check"]("security_audit", "3.3.0") is False
    report.write_bytes(b"")
    meta["artifact_sha256"] = hashlib.sha256(b"").hexdigest()
    (evidence_dir / "security_audit.json").write_text(
        __import__("json").dumps(meta), encoding="utf-8"
    )
    assert gate["_evidence_check"]("security_audit", "3.3.0") is False
    meta["artifact_path"] = "../outside.txt"
    meta["artifact_sha256"] = "0" * 64
    (evidence_dir / "security_audit.json").write_text(
        __import__("json").dumps(meta), encoding="utf-8"
    )
    assert gate["_evidence_check"]("security_audit", "3.3.0") is False



def test_release_gate_code_set_comparison_rejects_missing_duplicate_and_extra_codes():
    import runpy
    from pathlib import Path
    gate_path = Path(__file__).resolve().parents[1] / "scripts" / "legal_release_gate.py"
    gate = runpy.run_path(str(gate_path))
    check = gate["_code_set_check"]
    assert check(["IN", "UK"], ["IN", "UK"], ["UK", "IN"]) is True
    assert check(["IN", "UK"], ["IN"], ["IN", "UK"]) is False
    assert check(["IN", "UK"], ["IN", "UK", "UK"], ["IN", "UK"]) is False
    assert check(["IN", "UK"], ["IN", "UK", "US"], ["IN", "UK"]) is False
