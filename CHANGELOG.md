# Version 3.5.0 - 2026-11-27

- Added named-statute source scoping to legal retrieval.
- Added regression tests for BNS and Indian Contract Act provision collisions.
- Corrected local-date handling in the legal evidence release gate.
- Refreshed official BNS and Indian Contract Act full-text sources in the local audit database.
- Verification: 182 automated tests passed; compilation and diff checks passed.
- Local database retrieval smoke checks: 4/4 passed.

The local corpus refresh is not included in this code commit unless separately configured and deployed through the project's approved data-release process.

Legal accuracy and production readiness are not certified.

---
## 3.3.1 — Statutory retrieval improvements

- Recognises full names of the Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha Sanhita and Bharatiya Sakshya Adhiniyam to reduce false clarification prompts.
- Improves retrieval of complete BNS statutory provisions across overlapping indexed chunks.
- Adds regression tests for BNS Section 303 retrieval and statutory-name recognition.
- This version remains a release candidate; automated tests do not certify legal accuracy or production readiness.
# Changelog

## 3.3.0 — Legal governance foundation and hardening

- Added a 52-jurisdiction source inventory with explicit unverified and missing-source statuses.
- Added versioned legal document, provision, temporal relation, ingestion provenance and jurisdiction hierarchy metadata tables.
- Added content-hash recording and conservative temporal metadata assessment.
- Added exact quote-presence checking, explicitly not semantic legal verification.
- Added legal coverage inventory API endpoints.
- Enabled SQLite foreign-key enforcement on every governance connection and added hierarchy cycle checks.
- Prevented metadata registration functions from self-declaring legal documents, versions or relations as verified.
- Added validation for relation dates, relation endpoints, ingestion status and ingestion metadata.
- Hardened the release gate to compare selector/source/benchmark jurisdiction code sets, reject duplicates, and require scoped, fresh, hash-matched evidence artifacts instead of environment-variable attestations.
- Evidence artifact checks do not cryptographically authenticate reviewer identity or independently prove the report's conclusions.
- Kept legal accuracy, security and production certification disabled until the required real-world evidence exists.

## 3.0.4 — Packaging cleanup
- Removed the retired `install_chat_history.py` stub and the obsolete `scripts/install_release_1_2_1.bat` / `install_release_2_0.bat` installers.
- Removed a duplicated, stale tail from this changelog.
- Version bumped to 3.0.4 across the app, tests, docs and release scripts. No functional code changes.

## 3.0.3 — Accuracy and consistency fixes
- Task routing: the substring "act" (and "law", "court", "tax", "suit", "itr") matched ordinary words such as "fact", "contract", "nitrogen" and "taxi", sending unrelated questions into strict legal retrieval. Short keywords now use whole-token matching; statute references ("IT Act", "Act, 2000") are still recognised.
- Context/citation consistency: retrieved excerpts were cut at a fixed character count, so sources S3-S5 could be listed as citations (and accepted as valid) although the model never received them. Sources are now fitted whole, truncation is marked, and only sources actually sent are returned as citations. Budget is tunable with `ARLAW_CONTEXT_CHARS` (default 4200).
- Citation parsing now accepts grouped labels such as `[S1, S2]`.
- The Delhi High Court (Naz Foundation) digest and registry entry used the unselectable jurisdiction code `IN-DELHI`, so they could never be retrieved or reported; both are now `IN`, and existing databases are repaired on startup.
- Ambiguity checks no longer demand an instrument name when one is plainly given (IPC, CrPC, IT Act, U.S.C., GDPR, lease/contract agreements, etc.).
- Ollama adapter strips inline `<think>` reasoning; Groq retry parsing handles compound durations such as `1m30.5s`.
- Frontend: readable error messages for validation/429/non-JSON failures, no pile-up of empty "New conversation" entries, translated interface labels now apply, registry links readable in light mode.
- Citation checks now cover prose paragraphs, each factual list item and each table row; quality warnings report uncited units, unknown labels and unverified source-to-claim support. The system prompt requires a source label on every factual legal proposition and forbids uncited cases/holdings when sources are supplied.
- Source URL hygiene: generic institution homepages are no longer stored as document-level citation URLs; existing rows are cleaned on startup.
- Abstention: when a question names a specific provision, case or numbered instrument and no jurisdiction-matched source is retrieved, the API declines to give a source-backed answer. Broad conceptual questions (and document review) are still answered, but are labelled as general, unverified information and instructed not to cite specifics.
- CI now installs `requirements-test.txt` (httpx is required by FastAPI's TestClient).
- Removed the retired `install_chat_history.py` patch and orphaned `history.js` (the patch overwrote the request-size safeguards) and stray `__pycache__` files from the package.

## 3.0.2 — Chat request and retrieval precision fixes
- Bound browser chat requests to the API's 30-message and 14,000-character limits, including long-running conversations.
- Tightened legal retrieval overlap so generic jurisdiction wording cannot cause unrelated case digests to appear as relevant support.
- Added PowerShell 5.1 API smoke tests and regression tests for request bounds and retrieval precision.
- Reconfirmed that an empty retrieval result is preferable to a misleading citation when the indexed corpus lacks a topic-specific source.

## 3.0.1 — Ambiguity and coverage transparency
- Added conservative clarification for underspecified agenda, resolution and provision references.
- Added `/api/coverage` as a registry inventory with explicit limits.

## 3.0.0 — Security baseline and deployment hygiene
- Preserved existing frontend, provider routing, knowledge retrieval, jurisdictions, source registry and local browser history.
- Added per-IP chat/upload throttling, strict request and jurisdiction validation, safer bounded document ingestion and response security headers.
- Documented persistent storage requirements and production security blockers; Render Free remains explicitly ephemeral.
- Cleaned the release package of credentials, databases, Git metadata, virtual environments, backups and caches.
- Added regression coverage for security headers, rate limits, role/jurisdiction validation and safe upload filenames.
- Not production-certified, legally certified or independently security-audited.


## 2.4.0 — Workspace redesign and personalization

- Refined responsive workspace styling and navigation presentation.
- Added 36 persistent accent-colour palettes alongside light/dark appearance.
- Expanded README with AI architecture, provider routing, retrieval details and explicit verification limitations.
- Exposed retrieval relevance as a search heuristic in source metadata; it is not claim-support verification.
- Updated application version to 2.4.0.


## 2.3.0 — Retrieval integrity and workspace refinement
- Added topic-aware source categories and a safe SQLite migration for earlier databases.
- Separated bundled law digests from economic/shortage frameworks during task-aware retrieval.
- Added stricter jurisdiction filtering, query-term relevance ranking and duplicate-source collapse.
- Improved citation label parsing for `[S#]` and `**S#**`; metadata now explicitly states that existence is not source-support verification.
- Added browser-local recent chat history, request/loading feedback and responsive interface refinements.
- Preserved configurable Ollama-first/Groq-fallback routing.
- Added regression tests for legacy database migration, topic separation, jurisdiction filtering and citation formatting.
- This release is not legally certified, production-certified or security-audited.

## 2.1.0 — Reliability and response integrity
- Detects repeated paragraphs and section descriptions in generated answers.
- Makes one bounded rewrite attempt when repetition is detected; unresolved repetition is surfaced as a visible reliability warning.
- Continues a response only when the provider explicitly reports token-limit truncation, with a maximum of two continuation calls.
- Exposes quality, continuation and incomplete-response metadata through the chat API.
- Adds regression tests for repeated legal sections, rewrite recovery and truncated-response continuation.
- Preserves the existing UI, knowledge base, Groq-only provider configuration and direct Python launch workflow.
- This release does not certify legal accuracy; legal provisions still require verification against current primary sources.

## 2.0.0 — Final Stable Package
- Consolidated current application capabilities and release documentation.
- Added guarded Windows integration script with backup and protected local files (retired in 3.0.4).
- Documented automated verification, release boundaries and maintenance policy.
- Preserved existing backend, frontend, provider configuration and project workflows.


## 3.0.5 — 2026-11-25

- Strengthened legal-source hierarchy instructions: primary legal text and secondary digests must be distinguished.
- Prevented the assistant from describing a digest as an official judgment or statute.
- Added a safeguard against presenting an older decision as current law unless retrieved sources establish subsequent developments.
- Required conflicts and incomplete evidence to be surfaced rather than silently resolved.
- These are generation safeguards; they do not independently verify source relevance, legal correctness, or currency.

## 3.1.1 — 2026-11-25
- Added jurisdiction-specific legal digests for Article 21, privacy/data protection, corporate fraud and officer liability, competition, trade controls and sanctions.
- Added five-question global coverage regression tests and international sanctions retrieval routing.
- Added an explicit evidence gate for precise penalties, fines, imprisonment terms, limitation periods, effective dates, thresholds and percentages.
- Added a visible quality warning when generated legal answers contain precise penalty/deadline/threshold figures; this is a warning heuristic, not claim-level verification.
- Added a legal accuracy benchmark protocol. Legal accuracy remains not independently measured; no accuracy percentage is claimed.
- Corrected the test dependency name from `httpx2` to `httpx`.
- Automated regression suite: 122 passed in the prepared source tree. This is not a legal accuracy score.

