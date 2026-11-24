# ARLAW AI Global 3.0.7 — provision-aware retrieval precision

## Changes
- Detects explicit Article/Section references in legal research prompts.
- Requires retrieved passages to contain the requested provision reference or a plausible provision heading.
- Gives stronger ranking weight to provision headings in legislative text, while filtering common Schedule/Appendix numbering collisions.
- Expands the candidate pool for explicitly numbered provisions so long structured prompts are less likely to crowd out the requested primary text.
- Adds regression tests that inspect the retrieved passage text, not just the source title.
- Updates the API health/version metadata to 3.0.7.
- Repairs the optional `check_groq.py` connectivity diagnostic so the project can pass source compilation checks.

## Verified in the review copy
- `pytest -q`: 98 passed.
- `compileall` for `app`, `tests`, and `check_groq.py`: to be verified after packaging.

## Scope and limitations
- This is a retrieval-quality correction, not new legal training or new legal-source coverage.
- The existing database is not modified by this patch.
- The country selector and official-source directory remain starting points, not evidence of comprehensive legal coverage.
- Passage-level ranking is still heuristic; citations still require human verification.
- This release is not production-certified, legal-accuracy-certified, or security-audited.
