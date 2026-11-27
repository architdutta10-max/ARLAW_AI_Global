"""Fail-closed legal release gate with evidence-artifact and manifest validation.

Evidence metadata is checked for completeness, scope, freshness and report hash.
This does not authenticate reviewer identity or prove the underlying review was
independent; those remain human/process controls.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "release_evidence"
MAX_EVIDENCE_AGE_DAYS = 365


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _selector_codes() -> list[str]:
    selector = _load_json(ROOT / "app" / "jurisdictions.json")
    return [
        str(item["code"]).strip().upper()
        for group in selector.get("groups", [])
        for item in group.get("items", [])
    ]


def _code_set_check(expected: list[str], *actual_lists: list[str]) -> bool:
    if not expected or len(expected) != len(set(expected)):
        return False
    expected_set = set(expected)
    for actual in actual_lists:
        if not actual or len(actual) != len(set(actual)) or set(actual) != expected_set:
            return False
    return True


def _evidence_check(kind: str, version: str) -> bool:
    """Validate a JSON attestation and a separate, in-repository evidence artifact."""
    metadata_path = ROOT / "release_evidence" / f"{kind}.json"
    if not metadata_path.is_file():
        return False
    try:
        meta = _load_json(metadata_path)
        required = ("status", "reviewer", "reviewer_qualification", "reviewed_at",
                    "scope_version", "artifact_path", "artifact_sha256")
        if any(not str(meta.get(k, "")).strip() for k in required):
            return False
        if meta["status"] != "passed" or meta["scope_version"] != version:
            return False
        reviewed = date.fromisoformat(meta["reviewed_at"])
        age = (date.today() - reviewed).days
        if age < 0 or age > MAX_EVIDENCE_AGE_DAYS:
            return False
        artifact = (ROOT / meta["artifact_path"]).resolve()
        if ROOT.resolve() not in artifact.parents or not artifact.is_file() or artifact.stat().st_size == 0:
            return False
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        return digest.lower() == str(meta["artifact_sha256"]).lower()
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False


def evaluate():
    source = _load_json(ROOT / "app" / "legal_source_manifest.json")
    benchmarks = _load_json(ROOT / "evaluation" / "jurisdiction_benchmark_manifest.json")
    version_data = _load_json(ROOT / "VERSION.json")
    version = str(version_data.get("version", ""))
    selector_codes = _selector_codes()
    source_rows = source.get("jurisdictions", [])
    benchmark_rows = benchmarks.get("jurisdictions", [])
    source_codes = [str(x.get("code", "")).strip().upper() for x in source_rows]
    benchmark_codes = [str(x.get("code", "")).strip().upper() for x in benchmark_rows]

    code_sets_match = _code_set_check(selector_codes, source_codes, benchmark_codes)
    coverage_verified = (
        code_sets_match and bool(source_rows)
        and all(x.get("verified_legal_coverage") is True
                and x.get("coverage_status") == "verified"
                and bool(x.get("sources"))
                and all(s.get("verification_status") == "verified" for s in x["sources"])
                for x in source_rows)
    )
    benchmarks_passed = (
        code_sets_match and bool(benchmark_rows)
        and all(x.get("benchmark_status") == "passed"
                and x.get("frozen_source_pack") is True
                and x.get("independent_answer_key") is True
                and isinstance(x.get("reviewer_scores"), dict)
                and bool(x["reviewer_scores"])
                for x in benchmark_rows)
    )
    checks = {
        "selector_source_and_benchmark_code_sets_match_without_duplicates": code_sets_match,
        "all_selector_jurisdictions_have_verified_legal_sources": coverage_verified,
        "all_jurisdictions_have_frozen_benchmarks_and_independent_answer_keys": benchmarks_passed,
        "persistent_hosted_storage_verified": _evidence_check("persistence", version),
        "independent_security_audit_passed": _evidence_check("security_audit", version),
        "qualified_human_legal_review_approved": _evidence_check("human_legal_review", version),
        "release_metadata_certified": bool(version_data.get("legal_accuracy_certified"))
            and bool(version_data.get("production_certified"))
            and bool(version_data.get("security_audited")),
    }
    return {
        "release_ready": all(checks.values()),
        "checks": checks,
        "jurisdictions": len(selector_codes),
        "source_manifest_entries": len(source_rows),
        "benchmark_manifest_entries": len(benchmark_rows),
        "verified_legal_coverage": sum(
            1 for x in source_rows if x.get("verified_legal_coverage") is True
        ),
        "notice": (
            "A passing software test suite does not replace source verification, "
            "qualified legal review, security audit or hosted persistence validation. "
            "Evidence metadata/hash validation does not cryptographically authenticate "
            "reviewer identity or independently prove the report's conclusions."
        ),
    }


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["release_ready"] else 2)
