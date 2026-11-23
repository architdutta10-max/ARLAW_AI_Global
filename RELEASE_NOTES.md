# ARLAW AI Global 2.3.0 — Release notes

## Retrieval and legal-source integrity
- Added source categories (`law`, `economy`, `general`) with a migration for existing SQLite databases.
- Bundled case digests and economic/shortage frameworks are separated during task-aware retrieval.
- Search now filters unrelated jurisdictions instead of silently falling back to unrelated jurisdictions.
- Retrieval ranks by query-term coverage, gives a modest title/jurisdiction preference, and collapses duplicate chunks from the same source.
- Citation checker recognises `[S#]` and `**S#**`, and reports only reference-label existence. It does not validate legal propositions, source support, source currency or authority.

## Interface
- Added browser-local recent chat history (up to 10 conversations, stored in localStorage on this device).
- Added request status and loading feedback; disables the composer while a request is in progress.
- Refined layout, focus indicators, responsive history list, citation notices and dark-mode presentation.

## Model routing
- Existing configurable Ollama/Groq preference order and fallback are retained.
- No provider key is included. No provider availability or answer correctness is guaranteed.

## Boundaries
- Bundled landmark-case records are curated secondary educational digests, not full official judgments.
- Economic/shortage records are research frameworks, not live datasets or alerts.
- No foundation model weights were retrained. Retrieval augmentation is not fine-tuning.
- This release is not legally certified, production-certified or independently security-audited.
