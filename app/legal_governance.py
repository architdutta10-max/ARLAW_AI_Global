"""Legal governance metadata, source coverage inventory and temporal provenance.

This module deliberately does not certify source URLs or infer that a registered
source provides complete law. It supplies auditable structures and fail-closed
coverage reporting for later verified ingestion.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .config import DB_PATH

MANIFEST_PATH = Path(__file__).with_name("legal_source_manifest.json")
JURISDICTIONS_PATH = Path(__file__).with_name("jurisdictions.json")


def _connect():
    """Open a governance connection with referential integrity enforced."""
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _validate_status(value: str, field_name: str) -> str:
    allowed = {"unverified", "pending_review", "rejected"}
    if value not in allowed:
        raise ValueError(
            f"{field_name} must be one of {sorted(allowed)}; "
            "'verified' requires a separate authenticated review workflow"
        )
    return value


def _validate_optional_date(value: str | None, field_name: str) -> None:
    if value is None or value == "":
        return
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{field_name} must be YYYY-MM-DD")


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def init_governance_db() -> None:
    """Create additive tables; never rewrite or delete existing source/chunk rows."""
    with _connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS jurisdiction_nodes (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            parent_code TEXT,
            node_type TEXT NOT NULL DEFAULT 'national_or_territorial',
            territorial_scope TEXT NOT NULL DEFAULT 'unspecified',
            coverage_status TEXT NOT NULL DEFAULT 'unverified',
            verified_at TEXT,
            FOREIGN KEY(parent_code) REFERENCES jurisdiction_nodes(code)
        );
        CREATE TABLE IF NOT EXISTS legal_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_key TEXT NOT NULL UNIQUE,
            jurisdiction_code TEXT NOT NULL,
            title TEXT NOT NULL,
            document_type TEXT NOT NULL DEFAULT 'unspecified',
            official_url TEXT NOT NULL DEFAULT '',
            source_id INTEGER,
            authority_tier TEXT NOT NULL DEFAULT 'unverified',
            language TEXT NOT NULL DEFAULT 'und',
            verification_status TEXT NOT NULL DEFAULT 'unverified',
            territorial_scope TEXT NOT NULL DEFAULT 'unspecified',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(source_id) REFERENCES sources(id)
        );
        CREATE TABLE IF NOT EXISTS legal_document_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            version_label TEXT NOT NULL DEFAULT '',
            publication_date TEXT,
            effective_from TEXT,
            effective_to TEXT,
            retrieved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            content_sha256 TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'unverified',
            supersedes_version_id INTEGER,
            notes TEXT NOT NULL DEFAULT '',
            UNIQUE(document_id, content_sha256),
            FOREIGN KEY(document_id) REFERENCES legal_documents(id),
            FOREIGN KEY(supersedes_version_id) REFERENCES legal_document_versions(id)
        );
        CREATE TABLE IF NOT EXISTS legal_provisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_id INTEGER NOT NULL,
            provision_ref TEXT NOT NULL,
            heading TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL,
            anchor TEXT NOT NULL DEFAULT '',
            content_sha256 TEXT NOT NULL,
            UNIQUE(version_id, provision_ref, content_sha256),
            FOREIGN KEY(version_id) REFERENCES legal_document_versions(id)
        );
        CREATE TABLE IF NOT EXISTS legal_version_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_version_id INTEGER NOT NULL,
            to_version_id INTEGER NOT NULL,
            relation_type TEXT NOT NULL CHECK(relation_type IN
                ('amends','repeals','replaces','commences','suspends','saves','overrules','distinguishes','affirms','interprets')),
            instrument_reference TEXT NOT NULL DEFAULT '',
            effective_on TEXT,
            verification_status TEXT NOT NULL DEFAULT 'unverified',
            verified_by TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(from_version_id) REFERENCES legal_document_versions(id),
            FOREIGN KEY(to_version_id) REFERENCES legal_document_versions(id)
        );
        CREATE TABLE IF NOT EXISTS source_ingestion_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            source_url TEXT NOT NULL,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            status TEXT NOT NULL DEFAULT 'started',
            http_status INTEGER,
            content_sha256 TEXT,
            extracted_characters INTEGER NOT NULL DEFAULT 0,
            error TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(document_id) REFERENCES legal_documents(id)
        );
        CREATE TABLE IF NOT EXISTS legal_evidence_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            jurisdiction_code TEXT NOT NULL,
            check_type TEXT NOT NULL,
            status TEXT NOT NULL,
            details_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_legal_docs_jurisdiction ON legal_documents(jurisdiction_code);
        CREATE INDEX IF NOT EXISTS idx_legal_versions_effective ON legal_document_versions(effective_from,effective_to);
        CREATE INDEX IF NOT EXISTS idx_legal_provisions_ref ON legal_provisions(provision_ref);
        CREATE INDEX IF NOT EXISTS idx_legal_relations_from ON legal_version_relations(from_version_id);
        """)
        manifest = load_manifest()
        parent_map = {"ENG-WAL": "UK", "SCO": "UK", "NIR": "UK"}
        for item in manifest.get("jurisdictions", []):
            code = item["code"]
            node_type = item.get("jurisdiction_type", "national_or_territorial")
            if code in parent_map:
                node_type = "regional"
            elif node_type == "national_or_territorial":
                node_type = "national"
            c.execute("""
                INSERT INTO jurisdiction_nodes(code,name,parent_code,node_type,territorial_scope,coverage_status)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(code) DO UPDATE SET
                  name=excluded.name,
                  parent_code=excluded.parent_code,
                  node_type=excluded.node_type,
                  coverage_status=excluded.coverage_status
            """, (
                code, item["name"], parent_map.get(code), node_type,
                "selector-level only; subnational scope not modelled",
                item.get("coverage_status", "unverified")
            ))


def coverage_report() -> dict[str, Any]:
    manifest = load_manifest()
    rows = manifest.get("jurisdictions", [])
    return {
        "schema_version": manifest.get("schema_version"),
        "notice": manifest.get("notice"),
        "selector_count": len(rows),
        "verified_legal_coverage_count": sum(bool(x.get("verified_legal_coverage")) for x in rows),
        "unverified_registry_candidate_count": sum(x.get("coverage_status") == "unverified_registry_candidates" for x in rows),
        "no_registered_source_count": sum(x.get("coverage_status") == "no_registered_legal_source" for x in rows),
        "jurisdictions": rows,
        "production_coverage_certified": False,
    }


def jurisdiction_source_inventory(code: str) -> dict[str, Any]:
    normalized = (code or "").strip().upper()
    for item in load_manifest().get("jurisdictions", []):
        if item["code"] == normalized:
            return item
    raise KeyError(normalized)


def register_document(
    *, document_key: str, jurisdiction_code: str, title: str,
    document_type: str, official_url: str, authority_tier: str,
    language: str = "und", verification_status: str = "unverified",
    territorial_scope: str = "unspecified", source_id: int | None = None,
) -> int:
    """Register metadata only; callers must verify source identity independently."""
    if not document_key.strip() or not title.strip():
        raise ValueError("document_key and title are required")
    verification_status = _validate_status(verification_status, "verification_status")
    code = jurisdiction_code.strip().upper()
    if code not in {x["code"] for x in load_manifest()["jurisdictions"]}:
        raise ValueError("Unsupported jurisdiction code")
    with _connect() as c:
        cur = c.execute("""
            INSERT INTO legal_documents(document_key,jurisdiction_code,title,document_type,
                official_url,source_id,authority_tier,language,verification_status,territorial_scope)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(document_key) DO UPDATE SET
                jurisdiction_code=excluded.jurisdiction_code,title=excluded.title,
                document_type=excluded.document_type,official_url=excluded.official_url,
                source_id=excluded.source_id,authority_tier=excluded.authority_tier,
                language=excluded.language,verification_status=excluded.verification_status,
                territorial_scope=excluded.territorial_scope
        """, (document_key, code, title, document_type, official_url, source_id,
              authority_tier, language, verification_status, territorial_scope))
        row = c.execute("SELECT id FROM legal_documents WHERE document_key=?", (document_key,)).fetchone()
        return int(row["id"])


def record_document_version(
    document_id: int, content: bytes, *, version_label: str = "",
    publication_date: str | None = None, effective_from: str | None = None,
    effective_to: str | None = None, status: str = "unverified", notes: str = "",
) -> tuple[int, str]:
    """Store a content hash and temporal metadata; no dates are inferred."""
    if not content:
        raise ValueError("content must not be empty")
    status = _validate_status(status, "status")
    for field_name, field_value in (("publication_date", publication_date),
                                    ("effective_from", effective_from),
                                    ("effective_to", effective_to)):
        _validate_optional_date(field_value, field_name)
    if effective_from and effective_to and date.fromisoformat(effective_to) < date.fromisoformat(effective_from):
        raise ValueError("effective_to cannot precede effective_from")
    digest = hashlib.sha256(content).hexdigest()
    with _connect() as c:
        c.execute("""
            INSERT OR IGNORE INTO legal_document_versions(
                document_id,version_label,publication_date,effective_from,effective_to,
                content_sha256,status,notes)
            VALUES(?,?,?,?,?,?,?,?)
        """, (document_id, version_label, publication_date, effective_from, effective_to,
              digest, status, notes))
        row = c.execute(
            "SELECT id FROM legal_document_versions WHERE document_id=? AND content_sha256=?",
            (document_id, digest)
        ).fetchone()
        return int(row["id"]), digest


def add_provision(version_id: int, provision_ref: str, text: str, *,
                  heading: str = "", anchor: str = "") -> int:
    if not provision_ref.strip() or not text.strip():
        raise ValueError("provision_ref and text are required")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    with _connect() as c:
        c.execute("""
            INSERT OR IGNORE INTO legal_provisions(version_id,provision_ref,heading,text,anchor,content_sha256)
            VALUES(?,?,?,?,?,?)
        """, (version_id, provision_ref, heading, text, anchor, digest))
        row = c.execute("""
            SELECT id FROM legal_provisions
            WHERE version_id=? AND provision_ref=? AND content_sha256=?
        """, (version_id, provision_ref, digest)).fetchone()
        return int(row["id"])


def record_version_relation(from_version_id: int, to_version_id: int, relation_type: str, *,
                            instrument_reference: str = "", effective_on: str | None = None,
                            verification_status: str = "unverified", verified_by: str = "",
                            notes: str = "") -> int:
    if from_version_id == to_version_id:
        raise ValueError("A version cannot have a relation to itself")
    allowed_relations = {
        "amends", "repeals", "replaces", "commences", "suspends", "saves",
        "overrules", "distinguishes", "affirms", "interprets",
    }
    if relation_type not in allowed_relations:
        raise ValueError("Unsupported relation_type")
    verification_status = _validate_status(verification_status, "verification_status")
    _validate_optional_date(effective_on, "effective_on")
    with _connect() as c:
        cur = c.execute("""
            INSERT INTO legal_version_relations(from_version_id,to_version_id,relation_type,
                instrument_reference,effective_on,verification_status,verified_by,notes)
            VALUES(?,?,?,?,?,?,?,?)
        """, (from_version_id, to_version_id, relation_type, instrument_reference,
              effective_on, verification_status, verified_by, notes))
        return int(cur.lastrowid)



def register_jurisdiction_node(code: str, name: str, *, parent_code: str | None,
                              node_type: str, territorial_scope: str,
                              coverage_status: str = "unverified") -> None:
    """Add a state/province/territory/court node without assuming source coverage."""
    allowed = {"national", "state", "province", "territory", "court", "supranational", "regional"}
    if node_type not in allowed:
        raise ValueError("Unsupported jurisdiction node_type")
    normalized = code.strip().upper()
    if not normalized or not name.strip():
        raise ValueError("code and name are required")
    normalized_parent = parent_code.strip().upper() if parent_code else None
    if normalized_parent == normalized:
        raise ValueError("A jurisdiction node cannot be its own parent")
    if coverage_status not in {"unverified", "pending_review", "rejected"}:
        raise ValueError("coverage_status cannot be self-declared as verified")
    with _connect() as c:
        if normalized_parent and not c.execute(
            "SELECT 1 FROM jurisdiction_nodes WHERE code=?", (normalized_parent,)
        ).fetchone():
            raise ValueError("parent_code does not exist")
        # Walk upward from the proposed parent. Reaching this node would create a cycle.
        cursor = normalized_parent
        visited = set()
        while cursor:
            if cursor == normalized:
                raise ValueError("Jurisdiction hierarchy cycle detected")
            if cursor in visited:
                raise ValueError("Existing jurisdiction hierarchy contains a cycle")
            visited.add(cursor)
            parent_row = c.execute(
                "SELECT parent_code FROM jurisdiction_nodes WHERE code=?", (cursor,)
            ).fetchone()
            cursor = parent_row["parent_code"] if parent_row else None
        c.execute("""
            INSERT INTO jurisdiction_nodes(code,name,parent_code,node_type,territorial_scope,coverage_status)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(code) DO UPDATE SET name=excluded.name,parent_code=excluded.parent_code,
                node_type=excluded.node_type,territorial_scope=excluded.territorial_scope,
                coverage_status=excluded.coverage_status
        """, (normalized, name.strip(), normalized_parent,
              node_type, territorial_scope, coverage_status))


def record_ingestion_run(*, source_url: str, status: str, content: bytes | None = None,
                         document_id: int | None = None, http_status: int | None = None,
                         extracted_characters: int = 0, error: str = "") -> int:
    """Persist connector provenance and content hash; caller supplies actual HTTP outcome."""
    allowed_statuses = {"started", "completed", "failed", "partial"}
    if status not in allowed_statuses:
        raise ValueError("Unsupported ingestion status")
    if not source_url.strip():
        raise ValueError("source_url is required")
    if extracted_characters < 0:
        raise ValueError("extracted_characters cannot be negative")
    if http_status is not None and not 100 <= int(http_status) <= 599:
        raise ValueError("http_status must be between 100 and 599")
    digest = hashlib.sha256(content).hexdigest() if content is not None else None
    with _connect() as c:
        cur = c.execute("""
            INSERT INTO source_ingestion_runs(document_id,source_url,completed_at,status,http_status,
                content_sha256,extracted_characters,error)
            VALUES(?,?,CURRENT_TIMESTAMP,?,?,?,?,?)
        """, (document_id, source_url, status, http_status, digest,
              max(0, int(extracted_characters)), error[:2000]))
        return int(cur.lastrowid)

def assess_temporal_applicability(version_id: int, on_date: str) -> dict[str, Any]:
    """Return metadata status only; never infer legal effect from missing dates."""
    try:
        requested = date.fromisoformat(on_date)
    except (TypeError, ValueError):
        raise ValueError("on_date must be YYYY-MM-DD")
    with _connect() as c:
        row = c.execute("""
            SELECT effective_from,effective_to,status,version_label
            FROM legal_document_versions WHERE id=?
        """, (version_id,)).fetchone()
    if row is None:
        raise KeyError(version_id)
    if not row["effective_from"]:
        result = "unknown_missing_effective_from"
    elif date.fromisoformat(row["effective_from"]) > requested:
        result = "not_yet_effective_by_recorded_date"
    elif row["effective_to"] and date.fromisoformat(row["effective_to"]) < requested:
        result = "outside_recorded_effective_period"
    elif row["status"] != "verified":
        result = "date_range_matches_but_version_unverified"
    else:
        result = "date_range_matches_verified_metadata_only"
    return {
        "version_id": version_id, "requested_date": requested.isoformat(),
        "effective_from": row["effective_from"], "effective_to": row["effective_to"],
        "status": result,
        "legal_applicability_certified": False,
        "warning": "Metadata date matching is not a legal determination. Check commencement, amendments, savings, transitional provisions and judicial treatment.",
    }
