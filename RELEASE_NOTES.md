# ARLAW AI Global 3.0.4 — Release notes

See CHANGELOG.md for the 3.0.4 packaging cleanup and the 3.0.3 accuracy fixes.

## Preserved capabilities
- FastAPI backend and existing browser workspace, themes, accent palettes and local chat history.
- Groq and optional Ollama provider routing.
- SQLite/FTS5 knowledge retrieval, topic-aware categories and jurisdiction-aware filtering.
- Existing legal research, civil, accounting, tax, judicial research and professional workflow prompts.
- Existing source registry, citations metadata and document indexing for PDF, TXT and Markdown.

## Security and reliability baseline
- Per-IP in-process throttling for chat and document upload endpoints.
- Strict user/assistant message role validation and supported-jurisdiction validation.
- Bounded upload reads, UTF-8 validation, PDF encryption/page-count checks, extracted-text cap and generated upload storage names.
- Response security headers and no-store caching on API routes.
- Deployment documentation covers secret rotation, ephemeral Render Free storage and persistent-volume options.
- Clean distribution excludes `.env`, private databases, Git internals, virtual environments, backups and caches.

## Important limitations
- No user authentication, per-user authorization or data isolation is included in this release.
- Rate limiting is process-local, not shared across workers/instances.
- Render Free storage is ephemeral; SQLite and uploads are not durable across all restarts/redeploys.
- No malware scanning or independent security penetration test is included.
- Citation labels and paragraph coverage are not proof that a source supports a legal proposition.
- No foundation-model weights were trained. Retrieval augmentation is not fine-tuning.
- This release is not legally certified, production-certified or independently security-audited.


## Version 3.0.1 — Accuracy and global coverage safeguards

- Added a conservative ambiguity gate for numbered agenda, resolution, article and section references that lack identifying context.
- Ambiguous requests now return a clarification prompt without invoking the language model or presenting unsupported citations.
- Added `GET /api/coverage` to disclose which supported jurisdictions have source-registry starting points, with explicit limits on what that inventory means.
- Added regression tests for clarification behaviour and coverage reporting.


## Version 3.0.2 — Long-conversation request fix

- Browser chat requests now send at most the 30 messages accepted by the API.
- Previous message content is bounded to the API's 14,000-character per-message limit.
- The prompt input enforces the same character limit.
- Added a frontend regression test for these request bounds.
- Added a PowerShell smoke-test script that uses the actual `messages` request shape and jurisdiction codes.
- Legal retrieval now requires stronger query-term overlap for multi-term questions; a missing topic-specific source yields no retrieved citation rather than weakly related case digests.
