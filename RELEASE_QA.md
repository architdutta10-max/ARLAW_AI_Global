# ARLAW AI Global 3.1.3 — Release QA

## Automated checks

- `python -m pytest -q`: 135 passed.
- `node --check app/static/app.js`: passed.
- `python -m compileall -q app tests`: passed.
- Five fixed legal-retrieval regression prompts: all expected jurisdictions returned topic-matched source records; all retrieved excerpts fit within the configured 10,000-character context budget.
- Bundled knowledge seed: 44 source records, including EU-scoped GDPR and Dual-Use Regulation digests.

## Scope and limitations

- Selective chat deletion remains browser-local (localStorage); it is not server-side deletion or cross-device synchronization.
- Retrieval tests validate source discovery and routing only. They do not validate the generated legal answer, legal correctness, source authenticity, or current validity.
- The bundled GDPR and dual-use additions are secondary research digests linked to official EUR-Lex texts, not substitutes for the primary legislation.
- No independent legal-professional review or statistically validated accuracy benchmark has been completed.
- This release is not production-certified and has not been pushed to GitHub or deployed to Render.
