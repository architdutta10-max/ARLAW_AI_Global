# ARLAW 3.2.0 — Full Legal Accuracy Upgrade Audit (Phase 1)

Baseline archive: `ARLAW_320_ACCURACY_AUDIT_BASELINE.zip`
Baseline SHA-256: `17840a33f0f5884c7a709973ff2c26d79c24b705a005ffa652216c84f47e4422`
Version in archive: 3.2.0

## Integrity and baseline tests

- ZIP integrity: passed.
- Extracted files: 85.
- Baseline test suite: 145 passed.
- The baseline version metadata explicitly states `legal_accuracy_certified: false`,
  `production_certified: false`, and `security_audited: false`.

## Findings

1. `app/jurisdictions.json` lists 52 selectable jurisdiction entries. It is a selector,
   not proof of legal-source coverage.
2. `app/sources_registry.json` has source entries for only 12 jurisdiction codes
   intersecting the selector. Forty selector entries have no matching registry entry.
   Some registered entries are broad/global/international frameworks rather than
   national legislation or case-law repositories.
3. `app/main.py` originally used a hard-coded list of country-name/demonym regexes
   for GLOBAL routing. Many selectable jurisdictions (for example Brazil, Spain,
   Nigeria and UAE) were not detected by those markers.
4. Legal retrieval in `app/knowledge.py` filters to exact jurisdiction for legal tasks.
   This is safer than cross-country contamination, but it means missing corpus coverage
   produces no retrieved evidence.
5. In `app/main.py`, the original no-source abstention only applied when the question
   named a specific authority. Broad legal questions could still be answered from
   model memory with a warning. That is not a sufficient legal accuracy gate.
6. `app/llm.py` checks whether citation labels exist and counts citation formatting.
   It explicitly does not establish claim-level support, source authenticity, source
   currency, jurisdiction correctness or legal correctness.
7. The source metadata has `as_of` dates, but the implementation does not maintain a
   complete amendment, commencement, repeal, supersession or point-in-time law model.
8. The jurisdiction model does not represent the state/province/territory/court-level
   hierarchy needed for subnational legal systems (notably the US, Canada, Australia
   and the UK legal systems).
9. `render.yaml` documents that the free Render filesystem is ephemeral. The hosted
   corpus must be placed in persistent storage or an external managed database and
   verified after deployment.

## Phase 1 safety changes prepared

- GLOBAL routing now supplements existing aliases with names dynamically loaded from
  every entry in `app/jurisdictions.json`.
- More specific England and Wales, Scotland and Northern Ireland selectors are not
  broadened to the general UK selector when explicitly named.
- Legal tasks now abstain when retrieval is disabled or returns no legal sources,
  including broad conceptual questions. This is intentionally conservative: missing
  coverage should not be filled with model memory.
- Added tests for dynamic routing, multi-jurisdiction detection, UK sub-jurisdiction
  specificity and fail-closed legal abstention.

## Verification

- Baseline: 145 passed.
- Phase 1 modified tree: 150 passed.
- Registry-name routing probe: all 52 of 52 selector names mapped to their jurisdiction code.
- `python -m compileall -q app tests scripts`: passed.
- This phase does not add authoritative source corpora for missing jurisdictions,
  validate individual legal claims, or certify legal accuracy.

## Required next phases

1. Add a versioned source manifest for every supported jurisdiction, including
   official legislation/gazette, courts, regulators, source type, territorial scope,
   language, retrieval method, update frequency, effective-date model and licence/access
   constraints. Where a verified source is unavailable, mark coverage unavailable.
2. Extend data model to distinguish source document, version, provision, paragraph,
   court, decision, authority level, effective dates, publication dates, amendment,
   repeal and supersession relations.
3. Build country and subnational jurisdiction hierarchy. A country selector alone is
   insufficient for federal systems.
4. Implement source ingestion connectors and persistent hosted storage. Validate
   content hashes, text extraction, page/section anchors, duplicate versions and
   source provenance. Never infer legal authority from a URL domain alone.
5. Implement proposition-level citation verification against exact retrieved spans.
   Label existence and paragraph citation counts remain formatting checks only.
6. Implement date-aware legal applicability and precedent treatment, including
   commencement, amendments, repeal, saving/transitional clauses and overruling.
7. Build jurisdiction-stratified benchmark packs with frozen primary-source extracts,
   independently authored answer keys and qualified legal review.
8. Deploy only after all automated, retrieval, security and human-review gates pass.

## Release status

**Not ready for production legal reliance.** Phase 1 is a conservative safety and
routing improvement only. Legal accuracy remains unmeasured and uncertified.
