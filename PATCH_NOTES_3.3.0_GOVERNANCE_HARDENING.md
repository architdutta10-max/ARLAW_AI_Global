# ARLAW AI Global 3.3.0 — Governance hardening patch

## Included
- SQLite foreign-key enforcement on each governance DB connection.
- Jurisdiction hierarchy cycle protection.
- No self-declared `verified` status through metadata registration APIs.
- Relation and ingestion metadata validation.
- Exact selector/source-manifest/benchmark code-set matching, including duplicate detection.
- Release evidence files are required instead of environment-variable booleans. Evidence must be in-repository, non-empty, in scope, no older than 365 days, and SHA-256 matched.
- Additional regression tests and updated governance documentation.

## Validation performed on this source package
- `python -m compileall -q app tests scripts`: passed.
- `python -m pytest -q`: **166 passed**.
- `python scripts/legal_release_gate.py`: exit code 2, expected. Code-set check passes (52/52/52); legal source verification, benchmarks, hosted persistence, security audit, qualified legal review and certification remain false.

A Python runtime startup emitted a spreadsheet warm-up diagnostic unrelated to this project; compileall and pytest themselves completed successfully.

## Important limits
The evidence-file checker validates metadata and file integrity only. It does not authenticate reviewer identity, qualifications, independence, or the truth of an audit/review report. No passing evidence files have been created. Do not change certification flags or fabricate review evidence.

The uploaded source ZIP omitted `requirements-ml.txt`, although an existing test requires it. This package supplies an unpinned optional-dependency file containing the four package names asserted by that test (`tensorflow-cpu`, `tensorflow-hub`, `transformers`, `torch`). If your original file has version pins or additional platform-specific constraints, preserve that original file before extracting this package and restore it afterward.

## Apply
Extract this ZIP over a backed-up working copy of the project. Do not push or deploy until you have reviewed the diff and run the tests in your Windows environment.
