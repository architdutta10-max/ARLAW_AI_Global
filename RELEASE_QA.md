# ARLAW AI Global 2.1.0 — Release and QA status

## Automated checks performed for 2.1.0
- `PYTHONPATH=. python -m pytest -q`: 23 passed.
- `python -m compileall -q app run.py`: passed.
- ZIP integrity: checked after packaging.
- Live model/network test: not run; requires the user's configured Groq API key and network.

## Reliability safeguards
- Repeated paragraph/section detection.
- One bounded rewrite attempt.
- Visible warning if repetition remains.
- Finish-reason-based continuation, maximum two continuation calls.
- Missing legal provisions are instructed to be marked unverified, not guessed.

## Boundaries
This release is not certified for legal accuracy, production readiness or security. Citation-label validation checks label existence only; it does not prove that a source supports a claim or that the source is current. Human verification against official primary sources remains necessary.

---

# ARLAW AI Global 2.0.2 — Release and QA status

## Release intent

This is the feature-complete stable package for the currently implemented project scope. It consolidates the existing FastAPI backend, teal interface, provider adapters, task routing, retrieval, multilingual prompting, settings, Support page, documentation and automated checks. It is not a claim that future security patches, dependency updates, provider changes or legal-source updates will never be needed.

## Automated verification

Run from the project root:

```cmd
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest -q
python -m compileall -q app scripts evaluation
```

The test suite covers backend behavior and frontend source contracts. A passing suite does not prove legal accuracy, production security, accessibility conformance or real-browser behavior.

## Browser verification

Optional Playwright instructions are in `tests/FRONTEND_BROWSER_TESTING.md`. A real browser check has not been represented as completed by packaging this release.

## Safe Windows integration

1. Extract the ZIP.
2. Run `scripts\\install_release_2_0.bat` from the extracted project directory.
3. The script requires an existing Git repository with a clean working tree, displays its branch/remotes, asks for confirmation, creates a backup, preserves `.git`, `.env`, virtual environments and local `data`, installs dependencies and runs tests.
4. It does not commit, push, force-push, delete obsolete files, or modify GitHub directly.

Default target: `%USERPROFILE%\\OneDrive\\Desktop\\ARLAW_AI_Global`. To use another target, pass its path as the first argument.

## Known release limitations

- The app is an informational research assistant, not a law firm or substitute for a qualified legal professional.
- Citation-reference validation checks retrieved reference labels; it does not establish that a source substantiates each legal proposition.
- Legal databases, effective dates and jurisdiction coverage require ongoing curation and verification.
- Production use requires authentication, authorization, rate limiting, secure deployment, upload scanning, retention controls, audit logging, monitoring, backups and incident response.
- Provider availability, model behavior, API pricing and external services can change independently of this package.
- Browser-level testing and independent legal-domain benchmarking remain separate validation tasks.

## Release decision

Suitable as a consolidated development/stable handoff package for local evaluation. Do not represent it as production-certified, legally authoritative, or independently security-audited.
