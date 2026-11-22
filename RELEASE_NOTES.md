# ARLAW AI Global — Release 1.2.0

## Included
- Hybrid model gateway with Groq, local Ollama and OpenAI-compatible adapters.
- Task routing for legal research, civil procedure, advocate workflows, accounting, CA/tax, judicial research, document review, translation and general questions.
- Optional independent model review, clearly separated from verified conclusions.
- SQLite/FTS5 source library with jurisdiction, authority, language and as-of metadata.
- Document ingestion for text, Markdown and text-based PDF files.
- English, Hindi and Bengali interface options, dark/light themes and accessibility preferences.
- API input bounds for conversation count and message size; the chat endpoint accepts only user/assistant roles.
- Automated unit tests and a smoke-evaluation runner.

## Verification performed for this package
- Python compile check: passed.
- Automated tests: see the test result supplied with this release package.
- ZIP integrity: verified after packaging.

## Important limitations
This is a software release, not a certification of legal, tax, accounting or judicial accuracy. Citation validation confirms that a cited source label exists; it does not prove that the source supports the claim. The included evaluation runner is a smoke test, not a professional benchmark. Production deployment still requires authentication, authorization, rate limiting, encrypted transport/storage, backups, monitoring, privacy review and jurisdiction-specific expert evaluation.

## Upgrade
Back up your existing repository and `.env` first. Extract this archive into a separate folder, compare your local changes, then merge the files into your repository. Do not overwrite your `.env`, database or uploaded knowledge files.
