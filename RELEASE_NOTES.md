# ARLAW AI Global 2.1.0

## Reliability and response integrity

- Detects repeated paragraphs and repeated section descriptions in model output.
- Makes one bounded rewrite attempt when repeated content is detected.
- If repetition remains, returns a visible warning rather than silently presenting the output as clean.
- Uses the provider finish reason to continue responses only when generation stopped at the output-token limit.
- Caps continuation at two extra calls to avoid runaway generation.
- Exposes quality, continuation and incomplete-response metadata through `/api/chat`.
- Raises the default completion budget to 4096 tokens; configurable with `ARLAW_MAX_COMPLETION_TOKENS` (bounded to 512–8192).
- Adds explicit prompt rules for handling multiple legal provisions independently and marking missing provisions unverified.

## Preserved

- Existing teal UI and settings.
- Existing FastAPI backend and SQLite knowledge store.
- Existing Groq-only provider configuration; no Gemini added.
- Direct Python launch workflow; no batch-file requirement.

## Verification status

- Automated test suite: 23 passed.
- Python bytecode compilation: passed.
- Live Groq/network test: not run in this build environment.
- Legal accuracy, production readiness and security are not certified. Always verify legal provisions against current official primary sources.
