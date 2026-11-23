# ARLAW AI Global 2.3.0 — Release and QA status

## Automated checks run in the release workspace
- Python test suite: **35 passed** (`python -m pytest -q`).
- Python bytecode compilation: passed (`python -m compileall -q app run.py`).
- Frontend JavaScript syntax: passed (`node --check app/static/app.js`).
- FastAPI smoke checks: `/api/health`, `/api/health/model`, `/api/capabilities`, `/api/jurisdictions`, `/api/registry` and `/api/sources` returned HTTP 200 in the local test client.
- ZIP integrity: verified after packaging (see final release archive).
- Unit tests cover provider preference/fallback, citation-label parsing, topic separation, jurisdiction filtering, database seeding and frontend contract checks.

## Not run / not certified
- Live Ollama inference: not run in this packaging environment; requires Ollama, a downloaded model and a running local service.
- Live Groq inference: not run; requires the user's private API key and network access.
- Real-browser visual/accessibility testing: not run.
- Production security audit, penetration test and legal accuracy certification: not performed.

## Important limitations
- Citation checking verifies only whether a label exists in the retrieved set. It does not prove the cited source supports the claim, that the source is authoritative/current, or that the answer is legally correct.
- Bundled case digests are secondary summaries, not official full-text judgments.
- Economic/shortage frameworks are not live data feeds, forecasts or alerts.
- Search relevance is heuristic; no retrieval algorithm guarantees complete or error-free research.
- Browser-local chat history is stored in localStorage on one browser/device and is not encrypted or synced. Do not store confidential or privileged material in it.
- Before production use, add authentication, access control, rate limiting, HTTPS, secure secret handling, retention/deletion controls, audit logging, upload scanning, backups and monitoring.
