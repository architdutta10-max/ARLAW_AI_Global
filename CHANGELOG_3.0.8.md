# ARLAW AI Global 3.0.8

## Fixed
- A `GLOBAL` dropdown selection no longer forces an explicitly India-specific legal question to search only `GLOBAL` records. Explicitly named jurisdictions are detected per question and searched separately.
- Numbered `QUESTION 1` ... `QUESTION N` prompts are split into independent retrieval units so one jurisdiction or topic does not mask the others.
- Mixed economic/legal questions now prioritize legal retrieval when the section contains explicit legal or regulatory issues; words such as `economic` or `financial` no longer automatically suppress legal sources.
- API responses now include a per-question `retrieval_coverage` report showing jurisdictions searched and where indexed sources were or were not found.
- Retrieved context tells the model to answer supported sections independently and explicitly disclose gaps instead of treating a partial retrieval as complete global coverage.

## Safety and scope
- A user-selected specific jurisdiction remains authoritative; automatic routing only applies when the selected jurisdiction is `GLOBAL`.
- Exact jurisdiction matching remains in force for legal research. The change does not mix domestic legal sources across countries.
- This release does not add laws, judgments, regulations, or new indexed jurisdiction coverage.
- This release does not certify legal accuracy, production readiness, security, or completeness.

## Tests
- Adds regression coverage for an Article 21 query submitted with `GLOBAL` selected.
- Adds mixed-jurisdiction prompt routing tests, explicit jurisdiction override protection, legal-vs-economic task classification, and numbered question splitting.
