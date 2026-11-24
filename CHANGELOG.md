# Changelog

## 3.0.3 — Accuracy and consistency fixes
- Task routing: the substring "act" (and "law", "court", "tax", "suit", "itr") matched ordinary words such as "fact", "contract", "nitrogen" and "taxi", sending unrelated questions into strict legal retrieval. Short keywords now use whole-token matching; statute references ("IT Act", "Act, 2000") are still recognised.
- Context/citation consistency: retrieved excerpts were cut at a fixed character count, so sources S3-S5 could be listed as citations (and accepted as valid) although the model never received them. Sources are now fitted whole, truncation is marked, and only sources actually sent are returned as citations. Budget is tunable with `ARLAW_CONTEXT_CHARS` (default 4200).
- Citation parsing now accepts grouped labels such as `[S1, S2]`.
- The Delhi High Court (Naz Foundation) digest and registry entry used the unselectable jurisdiction code `IN-DELHI`, so they could never be retrieved or reported; both are now `IN`, and existing databases are repaired on startup.
- Ambiguity checks no longer demand an instrument name when one is plainly given (IPC, CrPC, IT Act, U.S.C., GDPR, lease/contract agreements, etc.).
- Ollama adapter strips inline `<think>` reasoning; Groq retry parsing handles compound durations such as `1m30.5s`.
- Frontend: readable error messages for validation/429/non-JSON failures, no pile-up of empty "New conversation" entries, translated interface labels now apply, registry links readable in light mode.
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

# Changelog

## 3.0.0 — Security baseline and deployment hygiene
- Preserved existing frontend, provider routing, knowledge retrieval, jurisdictions, source registry and local browser history.
- Added per-IP chat/upload throttling, strict request and jurisdiction validation, safer bounded document ingestion and response security headers.
- Documented persistent storage requirements and production security blockers; Render Free remains explicitly ephemeral.
- Cleaned the release package of credentials, databases, Git metadata, virtual environments, backups and caches.
- Added regression coverage for security headers, rate limits, role/jurisdiction validation and safe upload filenames.
- Not production-certified, legally certified or independently security-audited.


## 2.0.0 — Final Stable Package

- Consolidated current application capabilities and release documentation.
- Added guarded Windows integration script with backup and protected local files.
- Documented automated verification, release boundaries and maintenance policy.
- Preserved existing backend, frontend, provider configuration and project workflows.


## Integrated hybrid milestone

- Added task classification and task-specific provider routing.
- Added independent peer-review mode using additional configured providers.
- Added retrieved-reference label validation for `[S#]` citations.
- Updated health metadata and frontend connection status to show provider/model/task.
- Added a teacher-output distillation data preparation utility with expert approval and source provenance checks.
- Added API evaluation runner and tests for routing, fallback, citation references and peer review.
- Preserved the existing FastAPI application, static teal UI, SQLite/FTS knowledge store, deployment configuration and repository layout.

## User settings build
- Added a visible Settings control in the application header.
- Added persistent light/dark appearance preferences.
- Added English, Hindi, and Bengali interface labels.
- Added text-size, higher-contrast, and reduced-motion controls.
- Preferences remain local to the browser.


## Professional workspace expansion

- Added task routing for lawyer/advocate workflow assistance, accounting support, CA/tax research and neutral judicial research.
- Added `/api/capabilities` to expose supported workflows and professional boundaries.
- Added starter prompts for the four professional workflows.
- Added explicit human-review, source-verification and non-substitution safeguards.
- Updated GitHub Actions to run tests through `python -m pytest` with the repository root on `PYTHONPATH`.

## Release 1.2.0
- Consolidated the integrated professional-workspace release package.
- Added bounded, typed chat-message input validation and rejected unsupported message roles at the API boundary.
- Updated API release metadata and FastAPI startup lifecycle handling.
- Added release notes and a production-readiness checklist that clearly identifies security and evaluation work still required.

## 2.1.2
- Added conservative prompt budgeting for long conversations and multilingual content.
- Reduced default completion budget to 1,200 tokens (configurable, capped at 2,048).
- Serialized Groq calls within a worker and added one bounded HTTP 429 retry using provider reset guidance.
- Preserved existing provider configuration, API shape, UI and conversation storage.

## 2.2.0 — Global knowledge starter and Ollama
- Added local Ollama chat inference and configurable fallback with Groq.
- Added bundled, searchable educational digests of selected landmark decisions across multiple jurisdictions.
- Added economic change, food, energy, critical-material and supply-chain shortage research frameworks.
- Expanded official court and economic-data source directory.
- Clarified RAG versus fine-tuning and the limits of bundled summaries/current-data coverage.
