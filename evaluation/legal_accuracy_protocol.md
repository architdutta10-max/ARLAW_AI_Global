# Legal accuracy benchmark protocol (3.1.1)

## No unearned accuracy percentage

A passing pytest suite measures software behaviour, not legal correctness. Retrieval hit rate, citation-label validity, citation support, and substantive legal accuracy are separate metrics. The application must not display a legal-accuracy percentage unless a versioned benchmark has been independently adjudicated.

## Required benchmark design

For every case, freeze: (1) user question, (2) jurisdiction, (3) as-of date, (4) authoritative primary-source pack and exact relevant extracts, (5) independently written expected propositions, (6) disallowed/common-confusion propositions, and (7) scoring rubric. Store source URLs, retrieval date, statute version/commencement and reviewer identity outside public answer output.

## Scoring dimensions

- Jurisdiction and applicable-date correctness.
- Rule/holding accuracy against primary text.
- Elements, exceptions, defences and procedural requirements.
- Penalty/threshold/effective-date accuracy.
- Binding versus persuasive authority classification.
- Citation existence, pinpoint accuracy and proposition-level support.
- Appropriate uncertainty where the source pack is incomplete.

Score each dimension against a human-reviewed rubric. A citation label existing in the response is not evidence that it supports the proposition. A retrieval hit is not a correct legal answer.

## Release gate

1. Run the complete automated suite.
2. Run a fixed, jurisdiction-stratified answer set against a frozen primary-source pack.
3. Have two qualified legal reviewers independently score each answer; adjudicate disagreements.
4. Report sample size, jurisdiction mix, date, reviewer agreement, confidence intervals and each metric separately.
5. Block release on fabricated authorities, unsupported penalty figures, wrong jurisdiction, stale commencement dates, or materially misleading conclusions.

Until those steps are completed, report **legal accuracy: not yet independently measured**. Do not substitute a model's self-assessment or a small hand-picked sample for this benchmark.
