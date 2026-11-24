# ARLAW AI Global 3.0.0 — Release notes

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
