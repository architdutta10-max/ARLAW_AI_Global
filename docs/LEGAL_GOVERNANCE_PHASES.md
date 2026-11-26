# ARLAW 3.3.0 — Legal Governance Foundation

## What this release implements

This is a governance and data-model foundation, not a global legal corpus release.

### 1. Jurisdiction source inventory

`app/legal_source_manifest.json` contains one record for every selector entry in
`app/jurisdictions.json` (52 total). It is generated from the selector and the
existing `app/sources_registry.json`.

- 12 selector codes have one or more existing registry candidates.
- 40 selector codes have no jurisdiction-specific registry candidate.
- Every candidate is marked `unverified_starting_point`.
- No jurisdiction is marked as having verified legal coverage.
- Global economic datasets and supranational sources are not treated as national
  statutes or domestic case-law coverage.

A candidate URL is not proof that the page is official, current, complete,
machine-readable, licensed for reuse, or relevant to the required territorial scope.
These records must be reviewed before ingestion.

### 2. Versioned legal authority data model

Additive SQLite tables:
- `jurisdiction_nodes`
- `legal_documents`
- `legal_document_versions`
- `legal_provisions`
- `legal_version_relations`
- `source_ingestion_runs`
- `legal_evidence_checks`

They record document identity, jurisdiction, source URL, declared authority tier,
language, territorial scope, content hashes, publication/effective dates, provision
anchors, amendment/repeal/commencement/saving/overruling relations, and ingestion
outcomes. Existing `sources` and FTS chunks are not deleted or rewritten.

The `register_document`, `record_document_version`, `add_provision`,
`record_version_relation`, `register_jurisdiction_node`, and
`record_ingestion_run` functions are metadata primitives. They do not independently
authenticate legal sources or determine legal effect.

### 3. Temporal applicability gate

`assess_temporal_applicability` returns explicit statuses for missing dates,
out-of-range dates, and unverified version metadata. Even a matching date range is
not represented as a legal conclusion. Commencement notifications, amendments,
savings, transitional clauses, repeal and judicial treatment must be verified.

### 4. Evidence checking

`app/legal_evidence.py` provides exact quote-presence checking after whitespace and
case normalization. A match only establishes that supplied text appears in supplied
excerpts. It does not establish that the excerpt supports a proposition, is authentic,
is current, is binding, or states the law correctly.

The existing model citation-label validation remains a formatting/reference check.
No semantic claim-to-authority verification is claimed in this release.

### 5. API

- `GET /api/legal/coverage` returns the full 52-entry source inventory and counts.
- `GET /api/legal/jurisdictions/{code}/sources` returns one jurisdiction inventory.
- `/api/health` and `/api/capabilities` do not certify legal accuracy.

### 6. Subnational hierarchy

The database supports parent/child jurisdiction nodes and controlled node types
(state, province, territory, court, regional, national and supranational). England and
Wales, Scotland and Northern Ireland are seeded as children of the UK selector. The
current manifest otherwise seeds selector-level nodes only. US states, Canadian
provinces/territories, Australian states/territories and detailed court hierarchies
still require a reviewed authoritative registry and must not be assumed from country
selection. `register_jurisdiction_node` adds reviewed nodes without granting them
source coverage.

## Deployment and persistence

The app already supports `ARLAW_DATA_DIR` and `ARLAW_DB_PATH`. The default Render
service remains on the free plan and its filesystem is ephemeral. For a persistent
hosted corpus, attach a paid persistent disk mounted at `/var/data`, set
`ARLAW_DATA_DIR=/var/data`, and verify the database survives a redeploy. This release
does not change the Render plan or create a paid disk. Do not store privileged client
documents until authentication, authorization, encryption, retention, backup and
security reviews are complete.

## Verification status and remaining work

Automated checks cover schema creation, non-destructive metadata registration,
content hashes, date-metadata abstention, 52-entry inventory counts, hierarchy parent
validation, and exact quote presence. `evaluation/jurisdiction_benchmark_manifest.json`
is a 52-entry benchmark template, not completed benchmark evidence. Run
`python scripts/legal_release_gate.py`; it must block this release until every
source, benchmark, persistence, security and human-review gate is satisfied.

Still not implemented or not independently verified:
- 40 jurisdictions have no source candidates in the current registry.
- The 12 candidate sets are not verified or completeness-assessed.
- No automated official-source connectors are enabled by default.
- No full national/subnational statute and case-law corpora are supplied.
- No semantic proposition-level citation verification is implemented.
- No amendment/commencement/repeal/overruling graph is populated with verified legal
  events.
- No jurisdiction-stratified frozen benchmark with independent qualified reviewer
  scores has been completed.
- Persistent hosted storage has not been provisioned or tested.
- Security audit and production certification remain false.

**Release decision: not certified for production legal reliance. Do not deploy as a
claim of global legal accuracy.**


## 7. Governance hardening and release evidence

Every connection created by the governance module enables SQLite foreign-key
enforcement. Jurisdiction parent updates are checked for cycles. Metadata APIs
accept only `unverified`, `pending_review`, or `rejected` verification states;
they cannot self-declare a document or version verified. A separate authenticated
review workflow is not implemented, so this code intentionally has no shortcut
that marks records verified.

Version relations validate relation type, endpoints, self-relations and ISO dates.
Ingestion records validate status, source URL presence, HTTP status range and
non-negative extracted-character counts.

The release gate now compares the exact selector, source-manifest and benchmark
jurisdiction code sets and rejects duplicates. Persistence, security-audit and
human-legal-review checks require JSON metadata under `release_evidence/` plus a
separate evidence artifact whose SHA-256 matches. Metadata must include:
`status`, `reviewer`, `reviewer_qualification`, `reviewed_at`, `scope_version`,
`artifact_path`, and `artifact_sha256`. Artifacts must be inside the repository,
non-empty by virtue of being a file, and no more than 365 days old.

This is an integrity and completeness check, not a digital signature. It does not
authenticate reviewer identity, qualification, independence, or report conclusions.
Do not create placeholder passing evidence. The three evidence checks remain false
until actual hosted-persistence testing, an independent security audit, and
qualified human legal review have occurred. The legal-source and benchmark checks
also remain false until their underlying work is completed.

Run:
```powershell
python -m compileall -q app tests scripts
python -m pytest -q
python scripts/legal_release_gate.py
```
The release-gate command is expected to exit with code 2 while any required
certification evidence is missing.
